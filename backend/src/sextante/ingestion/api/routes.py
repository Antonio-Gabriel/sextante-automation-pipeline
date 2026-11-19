"""HTTP API of the ingestion module: upload and job status (02-arquitectura.md §6)."""

from typing import Annotated, Literal

from fastapi import APIRouter, File, Query, Request, Response, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.ingestion.application.manage_jobs import DeleteJob, ListJobs
from sextante.ingestion.application.read_invoice import ReadInvoice
from sextante.ingestion.application.records import InvoiceView
from sextante.ingestion.application.reprocess_invoice import ReprocessInvoice
from sextante.ingestion.application.resolve_entity import ResolveEntity
from sextante.ingestion.application.upload_invoices import (
    FileTooLargeError,
    IncomingFile,
    UploadInvoices,
    check_file_count,
)
from sextante.platform.coded_text import FlagResponse, coded_text
from sextante.platform.http_params import IdentifierPath
from sextante.platform.idempotency import JsonBody
from sextante.platform.idempotent_route import IDEMPOTENCY_KEY_DECLARED, run_idempotently
from sextante.platform.limits import MAX_PAGE_SIZE, MAX_RESOLUTION_NOTE_LENGTH, MAX_UPLOAD_BYTES
from sextante.platform.structured_logging import correlation_id_var

ingestion_router = APIRouter(prefix="/api")


class UploadResponse(BaseModel):
    """Output contract of an upload (SEC-08, SEC-18): no path, no digest, no file name."""

    model_config = ConfigDict(frozen=True)

    job_id: str
    status: str
    invoice_count: int
    existing_job_ids: list[str]
    # Earlier jobs that were deleted, and that this upload brought back.
    restored_job_ids: list[str]


class ReprocessResponse(BaseModel):
    """Output contract of a reprocessing request."""

    model_config = ConfigDict(frozen=True)

    invoice_id: str
    job_id: str


@ingestion_router.post("/invoices", status_code=202, response_model=UploadResponse)
async def upload_invoices(
    request: Request, files: Annotated[list[UploadFile], File()]
) -> UploadResponse:
    """Accept PDF or XLSX invoices and answer at once with the job that will code them.

    The file count is checked before any content is read, and each file is read only up to
    one byte past the size limit (03-seguranca.md §9.1, SEC-16).

    Example:
        POST /api/invoices (multipart, field "files") -> 202 {"job_id": "...", ...}
    """
    check_file_count(len(files))
    incoming = [await _read_bounded(upload) for upload in files]
    use_case: UploadInvoices = request.app.state.upload_invoices
    receipt = await use_case.execute(incoming, correlation_id_var.get())
    return UploadResponse(
        job_id=receipt.job_id,
        status=receipt.status.value,
        invoice_count=receipt.invoice_count,
        existing_job_ids=list(receipt.existing_job_ids),
        restored_job_ids=list(receipt.restored_job_ids),
    )


class JobListEntryResponse(BaseModel):
    """One job as listed (SEC-18): no file name, no path, no digest."""

    model_config = ConfigDict(frozen=True)

    job_id: str
    status: str
    created_at: str
    finished_at: str | None
    invoice_counts: dict[str, int]
    invoice_total: int


class JobListResponse(BaseModel):
    """One page of jobs, newest first. ``limit_truncated`` says the limit was capped."""

    model_config = ConfigDict(frozen=True)

    jobs: list[JobListEntryResponse]
    limit: int
    offset: int
    limit_truncated: bool


class JobDeletedResponse(BaseModel):
    """The job just deleted, or deleted before."""

    model_config = ConfigDict(frozen=True)

    job_id: str


@ingestion_router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    request: Request,
    limit: Annotated[int, Query(ge=1)] = MAX_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> JobListResponse:
    """Return the jobs not deleted, newest first, paginated with a server maximum.

    Example:
        GET /api/jobs?limit=20 -> {"jobs": [{"job_id": "...", "status": "completed"}], ...}
    """
    page_size = min(limit, MAX_PAGE_SIZE)
    use_case: ListJobs = request.app.state.list_jobs
    jobs = await use_case.execute(page_size, offset)
    return JobListResponse(
        jobs=[
            JobListEntryResponse(
                job_id=job.job_id,
                status=job.status,
                created_at=job.created_at,
                finished_at=job.finished_at,
                invoice_counts=job.invoice_counts,
                invoice_total=sum(job.invoice_counts.values()),
            )
            for job in jobs
        ],
        limit=page_size,
        offset=offset,
        limit_truncated=limit > MAX_PAGE_SIZE,
    )


@ingestion_router.delete(
    "/jobs/{job_id}", response_model=JobDeletedResponse, dependencies=[IDEMPOTENCY_KEY_DECLARED]
)
async def delete_job(
    request: Request, response: Response, job_id: IdentifierPath
) -> JobDeletedResponse:
    """Delete a finished job, softly: it leaves every read, its records stay.

    Uploading again one of its files brings it back, with its reviews.

    Example:
        DELETE /api/jobs/3f2a... (Idempotency-Key: ...) -> 200 {"job_id": "3f2a..."}
    """
    use_case: DeleteJob = request.app.state.delete_job

    async def operation(connection: AsyncConnection) -> tuple[int, JsonBody]:
        await use_case.execute(connection, job_id)
        return 200, {"job_id": job_id}

    answer = await run_idempotently(request, response, {}, operation)
    return JobDeletedResponse.model_validate(answer)


@ingestion_router.post(
    "/invoices/{invoice_id}/reprocess",
    status_code=202,
    response_model=ReprocessResponse,
    dependencies=[IDEMPOTENCY_KEY_DECLARED],
)
async def reprocess_invoice(
    request: Request,
    response: Response,
    invoice_id: IdentifierPath,
) -> ReprocessResponse:
    """Queue a failed invoice again; it is coded from its stored text (NFR-REL-002).

    Example:
        POST /api/invoices/3f2a.../reprocess -> 202 {"invoice_id": "...", "job_id": "..."}
    """
    use_case: ReprocessInvoice = request.app.state.reprocess_invoice

    async def operation(connection: AsyncConnection) -> tuple[int, JsonBody]:
        receipt = await use_case.execute(connection, invoice_id)
        return 202, {"invoice_id": receipt.invoice_id, "job_id": receipt.job_id}

    answer = await run_idempotently(request, response, {}, operation)
    return ReprocessResponse.model_validate(answer)


async def _read_bounded(upload: UploadFile) -> IncomingFile:
    content = await upload.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise FileTooLargeError(
            f"File is larger than {MAX_UPLOAD_BYTES} bytes. Expected at most that size."
        )
    return IncomingFile(display_name=upload.filename or "", content=content)


class EntityResolutionResponse(BaseModel):
    """A reviewer's resolution of the entity, as recorded."""

    model_config = ConfigDict(frozen=True)

    verdict: str
    note: str
    resolved_at: str


class EarlierInvoiceResponse(BaseModel):
    """The invoice a possible duplicate repeats."""

    model_config = ConfigDict(frozen=True)

    invoice_id: str
    invoice_number: str | None


class InvoiceResponse(BaseModel):
    """One invoice for the reviewer (SEC-18: explicit projection, no storage detail)."""

    model_config = ConfigDict(frozen=True)

    invoice_id: str
    job_id: str
    status: str
    status_reason: FlagResponse | None
    supplier_name: str | None
    supplier_nif: str | None
    invoice_number: str | None
    invoice_date: str | None
    currency: str | None
    billed_entity_detected: str | None
    entity_verdict: str | None
    entity_reason: FlagResponse | None
    entity_resolution: EntityResolutionResponse | None
    resolvable: bool
    target_sheet: str | None
    possible_duplicate_of: EarlierInvoiceResponse | None


@ingestion_router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def read_invoice(request: Request, invoice_id: IdentifierPath) -> InvoiceResponse:
    """Return an invoice's extracted header, entity decision, state and earlier copy.

    Example:
        GET /api/invoices/3f2a... -> {"status": "not_coded", "resolvable": true, ...}
    """
    use_case: ReadInvoice = request.app.state.read_invoice
    return _invoice_response(await use_case.execute(invoice_id))


def _invoice_response(view: InvoiceView) -> InvoiceResponse:
    header = view.header
    return InvoiceResponse(
        invoice_id=view.invoice_id,
        job_id=view.state.job_id,
        status=view.state.status.value,
        status_reason=coded_text("rejections", view.status_reason),
        supplier_name=header.supplier_name,
        supplier_nif=header.supplier_nif,
        invoice_number=header.invoice_number,
        invoice_date=header.invoice_date,
        currency=header.currency,
        billed_entity_detected=header.billed_entity_detected,
        entity_verdict=view.state.entity_verdict,
        entity_reason=_entity_reason(view),
        entity_resolution=_resolution_response(view),
        resolvable=view.state.awaits_entity_resolution(),
        target_sheet=header.target_sheet,
        possible_duplicate_of=_earlier_response(view),
    )


def _entity_reason(view: InvoiceView) -> FlagResponse | None:
    # Once a reviewer resolved the entity, the resolution is the reason (D-3.15).
    return None if view.resolution is not None else coded_text("flags", view.state.entity_reason)


def _resolution_response(view: InvoiceView) -> EntityResolutionResponse | None:
    resolution = view.resolution
    if resolution is None:
        return None
    return EntityResolutionResponse(
        verdict=resolution.verdict, note=resolution.note, resolved_at=resolution.resolved_at
    )


def _earlier_response(view: InvoiceView) -> EarlierInvoiceResponse | None:
    earlier = view.earlier
    if earlier is None:
        return None
    return EarlierInvoiceResponse(
        invoice_id=earlier.invoice_id, invoice_number=earlier.invoice_number
    )


class EntityResolutionRequest(BaseModel):
    """Input contract of an entity resolution: a verdict and a mandatory note (SEC-08)."""

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    resolution: Literal["MATCH", "NO_MATCH"]
    note: str = Field(min_length=1, max_length=MAX_RESOLUTION_NOTE_LENGTH)


@ingestion_router.post(
    "/invoices/{invoice_id}/entity-resolution",
    status_code=202,
    response_model=ReprocessResponse,
    dependencies=[IDEMPOTENCY_KEY_DECLARED],
)
async def resolve_entity(
    request: Request, response: Response, invoice_id: IdentifierPath, body: EntityResolutionRequest
) -> ReprocessResponse:
    """Resolve an ambiguous entity; the invoice is coded again from its stored text.

    Needs Idempotency-Key. The denylist is never changed (REQ-REV-006).

    Example:
        POST /api/invoices/3f2a.../entity-resolution {"resolution": "MATCH", "note": "..."}
    """
    use_case: ResolveEntity = request.app.state.resolve_entity

    async def operation(connection: AsyncConnection) -> tuple[int, JsonBody]:
        receipt = await use_case.execute(connection, invoice_id, body.resolution, body.note)
        return 202, {"invoice_id": receipt.invoice_id, "job_id": receipt.job_id}

    answer = await run_idempotently(request, response, body.model_dump(), operation)
    return ReprocessResponse.model_validate(answer)
