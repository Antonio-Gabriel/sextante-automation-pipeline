"""SQL access for jobs, invoices, headers and lines. Every method joins the caller's transaction."""

import json
from dataclasses import asdict
from datetime import datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.ingestion.application.records import (
    ClaimedJob,
    DuplicateContentError,
    EntityCheckRecord,
    JobLine,
    JobSummary,
    NewInvoice,
    QueuedInvoice,
)
from sextante.ingestion.domain.model import (
    ExtractedInvoice,
    ExtractedLine,
    StoredInvoice,
    StoredLine,
)
from sextante.ingestion.domain.normalization import normalize_extraction
from sextante.ingestion.domain.statuses import InvoiceStatus, JobStatus
from sextante.ingestion.infrastructure.tables import (
    INVOICE_HEADER_TABLE,
    INVOICE_LINE_TABLE,
    INVOICE_TABLE,
    JOB_TABLE,
)
from sextante.platform.text_normalization import normalize_for_comparison


class IngestionRepository:
    """Implements IngestionRepositoryPort and JobLinesReader with SQLAlchemy Core.

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
        """Record an accepted upload. The unique digest constraint guards idempotency.

        Raises:
            DuplicateContentError: when another upload recorded the same digest first.
        """
        row = asdict(invoice) | {"status": InvoiceStatus.QUEUED, "created_at": now.isoformat()}
        row["id"] = row.pop("invoice_id")
        try:
            await connection.execute(INVOICE_TABLE.insert().values(**row))
        except IntegrityError as error:
            raise DuplicateContentError(
                f"Content digest {invoice.content_digest} is already recorded."
            ) from error

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
        return (
            ClaimedJob(job_id=str(row.id), correlation_id=str(row.correlation_id))
            if claimed
            else None
        )

    async def queued_invoices(
        self, connection: AsyncConnection, job_id: str
    ) -> list[QueuedInvoice]:
        """Return the job's invoices still waiting, in upload order."""
        query = (
            select(INVOICE_TABLE.c.id, INVOICE_TABLE.c.storage_name, INVOICE_TABLE.c.file_format)
            .where(INVOICE_TABLE.c.job_id == job_id, INVOICE_TABLE.c.status == InvoiceStatus.QUEUED)
            .order_by(INVOICE_TABLE.c.created_at, INVOICE_TABLE.c.id)
        )
        rows = (await connection.execute(query)).all()
        return [
            QueuedInvoice(str(row.id), str(row.storage_name), str(row.file_format)) for row in rows
        ]

    async def set_invoice_status(
        self,
        connection: AsyncConnection,
        invoice_id: str,
        status: InvoiceStatus,
        reason: str | None = None,
    ) -> None:
        """Move an invoice to a status, with the reason when there is one."""
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
        """Persist header and lines, normalized first (REQ-ING-008), for coding to read."""
        normalized = normalize_extraction(extraction)
        header = _header_row(invoice_id, normalized)
        await connection.execute(INVOICE_HEADER_TABLE.insert().values(**header))
        paired = list(zip(line_ids, normalized.lines, strict=True))
        if paired:
            rows = [_line_row(invoice_id, line_id, line) for line_id, line in paired]
            await connection.execute(INVOICE_LINE_TABLE.insert(), rows)
        return StoredInvoice(
            invoice_id=invoice_id,
            supplier_name=normalized.supplier.name,
            currency=normalized.currency,
            billed_entities=normalized.billed_entities,
            lines=tuple(
                StoredLine(line_id, line.position, line.description) for line_id, line in paired
            ),
        )

    async def record_entity_check(
        self, connection: AsyncConnection, invoice_id: str, check: EntityCheckRecord
    ) -> None:
        """Record the entity verdict, its reason, and the routing decision (D-3.15)."""
        await connection.execute(
            update(INVOICE_HEADER_TABLE)
            .where(INVOICE_HEADER_TABLE.c.invoice_id == invoice_id)
            .values(
                entity_verdict=check.verdict,
                entity_reason=check.reason,
                target_sheet=check.target_sheet,
            )
        )

    async def job_summary(self, connection: AsyncConnection, job_id: str) -> JobSummary | None:
        """Return the job status and its invoice counts by status, or None if unknown."""
        status_query = select(JOB_TABLE.c.status).where(JOB_TABLE.c.id == job_id)
        status = (await connection.execute(status_query)).scalar_one_or_none()
        if status is None:
            return None
        counts_query = (
            select(INVOICE_TABLE.c.status, func.count())
            .where(INVOICE_TABLE.c.job_id == job_id)
            .group_by(INVOICE_TABLE.c.status)
        )
        counts = {
            str(row[0]): int(row[1]) for row in (await connection.execute(counts_query)).all()
        }
        return JobSummary(job_id=job_id, status=str(status), invoice_counts=counts)

    async def read_job_lines(
        self, connection: AsyncConnection, job_id: str, limit: int, offset: int
    ) -> list[JobLine]:
        """Return one page of the job's lines, by upload order then document position."""
        rows = (await connection.execute(_job_lines_query(job_id, limit, offset))).all()
        return [
            JobLine(
                line_id=str(r.id),
                invoice_number=r.invoice_number,
                position=int(r.position),
                description=str(r.description),
                billed_entity=_detected_entity(str(r.billed_entities)),
                entity_verdict=r.entity_verdict,
            )
            for r in rows
        ]


def _job_lines_query(job_id: str, limit: int, offset: int) -> Select[tuple[object, ...]]:
    lines, header = INVOICE_LINE_TABLE, INVOICE_HEADER_TABLE
    return (
        select(
            lines.c.id,
            header.c.invoice_number,
            lines.c.position,
            lines.c.description,
            header.c.billed_entities,
            header.c.entity_verdict,
        )
        .join(INVOICE_TABLE, INVOICE_TABLE.c.id == lines.c.invoice_id)
        .join(header, header.c.invoice_id == lines.c.invoice_id)
        .where(INVOICE_TABLE.c.job_id == job_id)
        .order_by(INVOICE_TABLE.c.created_at, INVOICE_TABLE.c.id, lines.c.position)
        .limit(limit)
        .offset(offset)
    )


def _detected_entity(billed_entities_json: str) -> str | None:
    # The billed entity as extracted, never normalized for comparison (REQ-ENT-006).
    # Several blocks are shown together, so a reviewer sees why the entity is ambiguous.
    names = [block["name"] for block in json.loads(billed_entities_json)]
    return " | ".join(names) if names else None


def _header_row(invoice_id: str, extraction: ExtractedInvoice) -> dict[str, object]:
    return {
        "invoice_id": invoice_id,
        "supplier_name": extraction.supplier.name,
        "supplier_nif": extraction.supplier.nif,
        "invoice_number": extraction.invoice_number,
        "invoice_date": extraction.invoice_date,
        "currency": extraction.currency,
        "billed_entities": json.dumps(
            [asdict(b) for b in extraction.billed_entities], ensure_ascii=False
        ),
        "summary_rows": json.dumps(
            [asdict(r) for r in extraction.summary_rows], ensure_ascii=False, default=str
        ),
        "notes": extraction.notes,
    }


def _line_row(invoice_id: str, line_id: str, line: ExtractedLine) -> dict[str, object]:
    return {
        "id": line_id,
        "invoice_id": invoice_id,
        "position": line.position,
        "description": line.description,
        "normalized_description": normalize_for_comparison(line.description),
        # Decimals are stored as text: SQLite has no exact decimal type (D-3.5).
        "quantity": _decimal_text(line.quantity),
        "unit_price": _decimal_text(line.unit_price),
        "vat_rate": _decimal_text(line.vat_rate),
        "amount": _decimal_text(line.amount),
    }


def _decimal_text(value: object) -> str | None:
    return None if value is None else str(value)
