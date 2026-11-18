"""HTTP API of the ingestion module: upload and job status (02-arquitectura.md §6)."""

from typing import Annotated

from fastapi import APIRouter, File, Path, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from sextante.ingestion.application.upload_invoices import (
    IncomingFile,
    UploadInvoices,
    UploadRejectedError,
)
from sextante.ingestion.infrastructure.repository import IngestionRepository
from sextante.platform.http_errors import error_response
from sextante.platform.limits import IDENTIFIER_MAX_LENGTH, MAX_UPLOAD_BYTES
from sextante.platform.structured_logging import correlation_id_var

ingestion_router = APIRouter(prefix="/api")


class UploadResponse(BaseModel):
    """Output contract of an upload (SEC-08, SEC-18): no path, no digest, no file name."""

    model_config = ConfigDict(frozen=True)

    job_id: str
    status: str
    invoice_count: int
    already_uploaded_count: int


class JobStatusResponse(BaseModel):
    """Output contract of a job status (REQ-PLT-001)."""

    model_config = ConfigDict(frozen=True)

    job_id: str
    status: str
    invoice_counts: dict[str, int]


@ingestion_router.post("/invoices", status_code=202, response_model=UploadResponse)
async def upload_invoices(
    request: Request, files: Annotated[list[UploadFile], File()]
) -> UploadResponse | JSONResponse:
    """Accept PDF or XLSX invoices and answer at once with the job that will code them.

    Example:
        POST /api/invoices (multipart, field "files") -> 202 {"job_id": "...", ...}
    """
    incoming = []
    for upload in files:
        content = await upload.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            return error_response(413, "errors.upload.too_large")
        incoming.append(IncomingFile(display_name=upload.filename or "", content=content))
    use_case: UploadInvoices = request.app.state.upload_invoices
    try:
        receipt = await use_case.execute(incoming, correlation_id_var.get())
    except UploadRejectedError as rejection:
        status_code = 415 if rejection.user_message_key == "errors.upload.unsupported_type" else 422
        return error_response(status_code, rejection.user_message_key)
    return UploadResponse(
        job_id=receipt.job_id,
        status=receipt.status,
        invoice_count=receipt.invoice_count,
        already_uploaded_count=receipt.already_uploaded_count,
    )


@ingestion_router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def read_job_status(
    request: Request, job_id: Annotated[str, Path(max_length=IDENTIFIER_MAX_LENGTH)]
) -> JobStatusResponse | JSONResponse:
    """Return the job status with its invoices counted by status.

    Example:
        GET /api/jobs/3f2a... -> {"status": "completed", "invoice_counts": {"encoded": 1}}
    """
    async with request.app.state.database_engine.connect() as connection:
        summary = await IngestionRepository().job_summary(connection, job_id)
    if summary is None:
        return error_response(404, "errors.job.not_found")
    return JobStatusResponse(
        job_id=summary.job_id, status=summary.status, invoice_counts=summary.invoice_counts
    )
