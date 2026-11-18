"""HTTP API of the ingestion module: upload and job status (02-arquitectura.md §6)."""

from typing import Annotated

from fastapi import APIRouter, File, Path, Request, UploadFile
from pydantic import BaseModel, ConfigDict

from sextante.ingestion.application.read_job_status import ReadJobStatus
from sextante.ingestion.application.upload_invoices import (
    FileTooLargeError,
    IncomingFile,
    UploadInvoices,
    check_file_count,
)
from sextante.platform.limits import IDENTIFIER_MAX_LENGTH, MAX_UPLOAD_BYTES
from sextante.platform.structured_logging import correlation_id_var

ingestion_router = APIRouter(prefix="/api")


class UploadResponse(BaseModel):
    """Output contract of an upload (SEC-08, SEC-18): no path, no digest, no file name."""

    model_config = ConfigDict(frozen=True)

    job_id: str
    status: str
    invoice_count: int
    existing_job_ids: list[str]


class JobStatusResponse(BaseModel):
    """Output contract of a job status (REQ-PLT-001)."""

    model_config = ConfigDict(frozen=True)

    job_id: str
    status: str
    invoice_counts: dict[str, int]


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


@ingestion_router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def read_job_status(
    request: Request, job_id: Annotated[str, Path(max_length=IDENTIFIER_MAX_LENGTH)]
) -> JobStatusResponse:
    """Return the job status with its invoices counted by status.

    Example:
        GET /api/jobs/3f2a... -> {"status": "completed", "invoice_counts": {"encoded": 1}}
    """
    read_status: ReadJobStatus = request.app.state.read_job_status
    summary = await read_status.execute(job_id)
    return JobStatusResponse(
        job_id=summary.job_id, status=summary.status, invoice_counts=summary.invoice_counts
    )


async def _read_bounded(upload: UploadFile) -> IncomingFile:
    content = await upload.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise FileTooLargeError(
            f"File is larger than {MAX_UPLOAD_BYTES} bytes. Expected at most that size."
        )
    return IncomingFile(display_name=upload.filename or "", content=content)
