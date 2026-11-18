"""HTTP API of the ingestion module: upload and job status (02-arquitectura.md §6)."""

from typing import Annotated, Literal

from fastapi import APIRouter, File, Request, Response, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.ingestion.application.reprocess_invoice import ReprocessInvoice
from sextante.ingestion.application.resolve_entity import ResolveEntity
from sextante.ingestion.application.upload_invoices import (
    FileTooLargeError,
    IncomingFile,
    UploadInvoices,
    check_file_count,
)
from sextante.platform.http_params import IdentifierPath
from sextante.platform.idempotency import JsonBody
from sextante.platform.idempotent_route import run_idempotently
from sextante.platform.limits import MAX_RESOLUTION_NOTE_LENGTH, MAX_UPLOAD_BYTES
from sextante.platform.structured_logging import correlation_id_var

ingestion_router = APIRouter(prefix="/api")


class UploadResponse(BaseModel):
    """Output contract of an upload (SEC-08, SEC-18): no path, no digest, no file name."""

    model_config = ConfigDict(frozen=True)

    job_id: str
    status: str
    invoice_count: int
    existing_job_ids: list[str]


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
    )


@ingestion_router.post(
    "/invoices/{invoice_id}/reprocess", status_code=202, response_model=ReprocessResponse
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


class EntityResolutionRequest(BaseModel):
    """Input contract of an entity resolution: a verdict and a mandatory note (SEC-08)."""

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    resolution: Literal["MATCH", "NO_MATCH"]
    note: str = Field(min_length=1, max_length=MAX_RESOLUTION_NOTE_LENGTH)


@ingestion_router.post(
    "/invoices/{invoice_id}/entity-resolution", status_code=202, response_model=ReprocessResponse
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
