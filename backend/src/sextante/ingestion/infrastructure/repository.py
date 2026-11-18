"""SQL access for jobs, invoices, headers and lines. Every method joins the caller's transaction."""

import json
from dataclasses import asdict
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.ingestion.application.records import (
    ClaimedJob,
    JobSummary,
    NewInvoice,
    QueuedInvoice,
)
from sextante.ingestion.domain.model import ExtractedInvoice, StoredInvoice, StoredLine
from sextante.ingestion.domain.statuses import InvoiceStatus, JobStatus
from sextante.ingestion.infrastructure.tables import (
    INVOICE_HEADER_TABLE,
    INVOICE_LINE_TABLE,
    INVOICE_TABLE,
    JOB_TABLE,
)
from sextante.platform.text_normalization import normalize_for_comparison, normalize_text_input


class IngestionRepository:
    """Implements IngestionRepositoryPort with SQLAlchemy Core.

    Example:
        await IngestionRepository().insert_job(connection, job_id, correlation_id, now)
    """

    async def insert_job(
        self, connection: AsyncConnection, job_id: str, correlation_id: str, now: datetime
    ) -> None:
        """Create a queued job."""
        await connection.execute(
            JOB_TABLE.insert().values(
                id=job_id,
                status=JobStatus.QUEUED,
                correlation_id=correlation_id,
                created_at=now.isoformat(),
            )
        )

    async def find_job_of_digest(self, connection: AsyncConnection, digest: str) -> str | None:
        """Return the job of the invoice with this content digest, if it was uploaded before."""
        query = select(INVOICE_TABLE.c.job_id).where(INVOICE_TABLE.c.content_digest == digest)
        return (await connection.execute(query)).scalar_one_or_none()

    async def insert_invoice(
        self, connection: AsyncConnection, invoice: NewInvoice, now: datetime
    ) -> None:
        """Record an accepted upload. The unique digest constraint guards idempotency."""
        await connection.execute(
            INVOICE_TABLE.insert().values(
                id=invoice.invoice_id,
                job_id=invoice.job_id,
                content_digest=invoice.content_digest,
                display_name=invoice.display_name,
                storage_name=invoice.storage_name,
                file_format=invoice.file_format,
                status=InvoiceStatus.QUEUED,
                created_at=now.isoformat(),
            )
        )

    async def claim_next_job(
        self, connection: AsyncConnection, worker_id: str, now: datetime
    ) -> ClaimedJob | None:
        """Atomically claim the oldest queued job; None when there is none or it was taken.

        The UPDATE only counts when rowcount is 1, so two workers never take the same job
        (D-3.4).
        """
        oldest = select(JOB_TABLE.c.id, JOB_TABLE.c.correlation_id).where(
            JOB_TABLE.c.status == JobStatus.QUEUED
        )
        row = (await connection.execute(oldest.order_by(JOB_TABLE.c.created_at).limit(1))).first()
        if row is None:
            return None
        claim = (
            update(JOB_TABLE)
            .where(JOB_TABLE.c.id == row.id, JOB_TABLE.c.status == JobStatus.QUEUED)
            .values(status=JobStatus.RUNNING, worker_id=worker_id, claimed_at=now.isoformat())
        )
        claimed = (await connection.execute(claim)).rowcount == 1
        return ClaimedJob(job_id=row.id, correlation_id=row.correlation_id) if claimed else None

    async def queued_invoices(
        self, connection: AsyncConnection, job_id: str
    ) -> list[QueuedInvoice]:
        """Return the job's invoices still waiting, in upload order."""
        query = (
            select(INVOICE_TABLE.c.id, INVOICE_TABLE.c.storage_name, INVOICE_TABLE.c.file_format)
            .where(INVOICE_TABLE.c.job_id == job_id, INVOICE_TABLE.c.status == InvoiceStatus.QUEUED)
            .order_by(INVOICE_TABLE.c.created_at, INVOICE_TABLE.c.id)
        )
        return [
            QueuedInvoice(
                invoice_id=str(row.id),
                storage_name=str(row.storage_name),
                file_format=str(row.file_format),
            )
            for row in (await connection.execute(query)).all()
        ]

    async def set_invoice_status(
        self,
        connection: AsyncConnection,
        invoice_id: str,
        status: InvoiceStatus,
        reason: str | None = None,
    ) -> None:
        """Move an invoice to a final status, with the reason when there is one."""
        await connection.execute(
            update(INVOICE_TABLE)
            .where(INVOICE_TABLE.c.id == invoice_id)
            .values(status=status, status_reason=reason)
        )

    async def finish_job(
        self, connection: AsyncConnection, job_id: str, status: JobStatus, now: datetime
    ) -> None:
        """Close the job with its final status."""
        await connection.execute(
            update(JOB_TABLE)
            .where(JOB_TABLE.c.id == job_id)
            .values(status=status, finished_at=now.isoformat())
        )

    async def store_extraction(
        self,
        connection: AsyncConnection,
        invoice_id: str,
        extraction: ExtractedInvoice,
        line_ids: list[str],
    ) -> StoredInvoice:
        """Persist header and lines, with text normalized before persisting (REQ-ING-008)."""
        await connection.execute(
            INVOICE_HEADER_TABLE.insert().values(**_header_row(invoice_id, extraction))
        )
        stored_lines = tuple(
            StoredLine(line_id, line.position, normalize_text_input(line.description))
            for line_id, line in zip(line_ids, extraction.lines, strict=True)
        )
        if stored_lines:
            await connection.execute(
                INVOICE_LINE_TABLE.insert(),
                [_line_row(invoice_id, stored, extraction) for stored in stored_lines],
            )
        return StoredInvoice(invoice_id, extraction.billed_entities, stored_lines)

    async def set_target_sheet(
        self, connection: AsyncConnection, invoice_id: str, target_sheet: str
    ) -> None:
        """Record the routing decision of the invoice."""
        await connection.execute(
            update(INVOICE_HEADER_TABLE)
            .where(INVOICE_HEADER_TABLE.c.invoice_id == invoice_id)
            .values(target_sheet=target_sheet)
        )

    async def job_summary(self, connection: AsyncConnection, job_id: str) -> JobSummary | None:
        """Return the job status and its invoice counts by status, or None if unknown."""
        status = (
            await connection.execute(select(JOB_TABLE.c.status).where(JOB_TABLE.c.id == job_id))
        ).scalar_one_or_none()
        if status is None:
            return None
        counts_query = (
            select(INVOICE_TABLE.c.status, func.count())
            .where(INVOICE_TABLE.c.job_id == job_id)
            .group_by(INVOICE_TABLE.c.status)
        )
        counts = {row[0]: row[1] for row in (await connection.execute(counts_query)).all()}
        return JobSummary(job_id=job_id, status=status, invoice_counts=counts)


def _header_row(invoice_id: str, extraction: ExtractedInvoice) -> dict[str, object]:
    return {
        "invoice_id": invoice_id,
        "supplier_name": _optional_text(extraction.supplier.name),
        "supplier_nif": extraction.supplier.nif,
        "invoice_number": _optional_text(extraction.invoice_number),
        "invoice_date": extraction.invoice_date,
        "currency": extraction.currency,
        "billed_entities": json.dumps(
            [asdict(block) for block in extraction.billed_entities], ensure_ascii=False
        ),
        "summary_rows": json.dumps(
            [asdict(row) for row in extraction.summary_rows], ensure_ascii=False, default=str
        ),
        "notes": normalize_text_input(extraction.notes),
    }


def _line_row(
    invoice_id: str, stored: StoredLine, extraction: ExtractedInvoice
) -> dict[str, object]:
    source = next(line for line in extraction.lines if line.position == stored.position)
    return {
        "id": stored.line_id,
        "invoice_id": invoice_id,
        "position": stored.position,
        "description": stored.description,
        "normalized_description": normalize_for_comparison(stored.description),
        "quantity": _decimal_text(source.quantity),
        "unit_price": _decimal_text(source.unit_price),
        "vat_rate": _decimal_text(source.vat_rate),
        "amount": _decimal_text(source.amount),
    }


def _optional_text(value: str | None) -> str | None:
    return None if value is None else normalize_text_input(value)


def _decimal_text(value: object) -> str | None:
    # Decimals are stored as text: SQLite has no exact decimal type (D-3.5).
    return None if value is None else str(value)
