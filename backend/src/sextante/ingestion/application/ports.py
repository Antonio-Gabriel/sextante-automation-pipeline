"""Repository port of the ingestion use cases. Every method joins the caller's transaction."""

from datetime import datetime
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.ingestion.application.records import (
    ClaimedJob,
    EntityCheckRecord,
    ExportInvoice,
    JobLine,
    JobSummary,
    NewInvoice,
    QueuedInvoice,
)
from sextante.ingestion.domain.model import ExtractedInvoice, StoredInvoice
from sextante.ingestion.domain.statuses import InvoiceStatus, JobStatus


class IngestionRepositoryPort(Protocol):
    """Port: persistence of jobs, invoices, headers and lines."""

    async def insert_job(
        self, connection: AsyncConnection, job_id: str, correlation_id: str, now: datetime
    ) -> None:
        """Create a queued job."""
        ...

    async def find_job_of_digest(self, connection: AsyncConnection, digest: str) -> str | None:
        """Return the job of an earlier upload with the same content digest."""
        ...

    async def insert_invoice(
        self, connection: AsyncConnection, invoice: NewInvoice, now: datetime
    ) -> None:
        """Record an accepted upload. Raises DuplicateContentError on a known digest."""
        ...

    async def claim_next_job(
        self, connection: AsyncConnection, worker_id: str, now: datetime
    ) -> ClaimedJob | None:
        """Atomically claim the oldest queued job."""
        ...

    async def queued_invoices(
        self, connection: AsyncConnection, job_id: str
    ) -> list[QueuedInvoice]:
        """Return the job's invoices still waiting."""
        ...

    async def set_invoice_status(
        self,
        connection: AsyncConnection,
        invoice_id: str,
        status: InvoiceStatus,
        reason: str | None = None,
    ) -> None:
        """Move an invoice to a status."""
        ...

    async def finish_job(
        self, connection: AsyncConnection, job_id: str, status: JobStatus, now: datetime
    ) -> None:
        """Close the job."""
        ...

    async def store_extraction(
        self,
        connection: AsyncConnection,
        invoice_id: str,
        extraction: ExtractedInvoice,
        line_ids: list[str],
    ) -> StoredInvoice:
        """Persist header and lines."""
        ...

    async def record_entity_check(
        self,
        connection: AsyncConnection,
        invoice_id: str,
        check: EntityCheckRecord,
    ) -> None:
        """Record the entity verdict, its reason, and the routing decision."""
        ...

    async def job_summary(self, connection: AsyncConnection, job_id: str) -> JobSummary | None:
        """Return the job status and its invoice counts."""
        ...


class JobLinesReader(Protocol):
    """Port, published to other modules: the invoice lines of a job, in document order."""

    async def read_job_lines(
        self, connection: AsyncConnection, job_id: str, limit: int, offset: int
    ) -> list[JobLine]:
        """Return one page of the job's lines, by upload order then document position."""
        ...


class InvoiceExportReader(Protocol):
    """Port, published to other modules: every invoice of a job, with its lines."""

    async def read_job_invoices(
        self, connection: AsyncConnection, job_id: str
    ) -> list[ExportInvoice]:
        """Return the job's invoices in upload order, each with its lines in document order."""
        ...
