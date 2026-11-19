"""Repository port of the ingestion use cases. Every method joins the caller's transaction."""

from datetime import datetime
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.ingestion.application.records import (
    ClaimedJob,
    EntityCheckRecord,
    EntityResolutionRecord,
    ExportInvoice,
    InvoiceState,
    InvoiceView,
    JobLine,
    JobListEntry,
    JobRemovalState,
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

    async def change_job_status(
        self, connection: AsyncConnection, job_id: str, current: JobStatus, new: JobStatus
    ) -> bool:
        """Move a job from ``current`` to ``new``; False when it was no longer ``current``."""
        ...

    async def finish_job(
        self, connection: AsyncConnection, job_id: str, status: JobStatus, now: datetime
    ) -> bool:
        """Close a claimed job; False when it was queued again meanwhile."""
        ...

    async def requeue_interrupted_jobs(self, connection: AsyncConnection) -> int:
        """Queue again the jobs a stopped process left claimed; return how many."""
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

    async def load_stored_invoice(
        self, connection: AsyncConnection, invoice_id: str
    ) -> StoredInvoice | None:
        """Return the stored extraction, or None when the invoice was never extracted."""
        ...

    async def entity_resolution(self, connection: AsyncConnection, invoice_id: str) -> str | None:
        """Return the verdict a reviewer chose for this invoice, or None."""
        ...

    async def earlier_invoice_with_same_number(
        self, connection: AsyncConnection, invoice_id: str
    ) -> str | None:
        """Return the first invoice uploaded before this one with its supplier and number."""
        ...

    async def record_possible_duplicate(
        self, connection: AsyncConnection, invoice_id: str, earlier_invoice_id: str
    ) -> bool:
        """Point the invoice at the earlier one; False when it already pointed there."""
        ...


class ReprocessingRepositoryPort(Protocol):
    """Port: find an invoice, put it back in the queue, and reload what was stored."""

    async def invoice_state(
        self, connection: AsyncConnection, invoice_id: str
    ) -> InvoiceState | None:
        """Return the invoice's job and status, or None when unknown."""
        ...

    async def requeue_invoice(
        self, connection: AsyncConnection, invoice_id: str, job_id: str
    ) -> None:
        """Queue the invoice again and reopen its job."""
        ...


class EntityResolutionRepositoryPort(ReprocessingRepositoryPort, Protocol):
    """Port: reprocessing, plus storing a reviewer's entity resolution (REQ-REV-006)."""

    async def record_entity_resolution(
        self, connection: AsyncConnection, invoice_id: str, resolution: EntityResolutionRecord
    ) -> bool:
        """Store the resolution; False when the invoice already had one."""
        ...


class JobLinesReader(Protocol):
    """Port, published to other modules: the invoice lines of a job, in document order."""

    async def read_job_lines(
        self, connection: AsyncConnection, job_id: str, invoice_id: str | None
    ) -> list[JobLine]:
        """Return the job's lines, or one invoice's, by upload order then document position."""
        ...

    async def line_belongs_to_invoice(
        self, connection: AsyncConnection, invoice_id: str, line_id: str
    ) -> bool:
        """True when the invoice line exists, is a line of this invoice, and its job is not
        deleted."""
        ...

    async def line_in_active_job(self, connection: AsyncConnection, line_id: str) -> bool:
        """True when the invoice line exists and its job is not deleted."""
        ...


class JobRecordsPort(Protocol):
    """Port: the list of jobs, and their soft delete and restoration."""

    async def list_jobs(
        self, connection: AsyncConnection, limit: int, offset: int
    ) -> list[JobListEntry]:
        """Return the jobs not deleted, newest first, with their invoices by status."""
        ...

    async def job_removal_state(
        self, connection: AsyncConnection, job_id: str
    ) -> JobRemovalState | None:
        """Return the job's status and whether it is deleted, or None when unknown."""
        ...

    async def mark_job_deleted(
        self, connection: AsyncConnection, job_id: str, now: datetime
    ) -> None:
        """Hide the job from every read; its rows stay."""
        ...

    async def restore_job(self, connection: AsyncConnection, job_id: str) -> bool:
        """Show a deleted job again. True when it was deleted."""
        ...


class InvoiceViewReader(Protocol):
    """Port: one invoice as a reviewer sees it."""

    async def read_invoice_view(
        self, connection: AsyncConnection, invoice_id: str
    ) -> InvoiceView | None:
        """Return the invoice's state, header, resolution and earlier copy, or None."""
        ...


class InvoiceExportReader(Protocol):
    """Port, published to other modules: every invoice of a job, with its lines."""

    async def read_job_invoices(
        self, connection: AsyncConnection, job_id: str
    ) -> list[ExportInvoice]:
        """Return the job's invoices in upload order, each with its lines in document order."""
        ...
