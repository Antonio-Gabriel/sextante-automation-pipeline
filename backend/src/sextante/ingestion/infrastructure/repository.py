"""SQL access for jobs, invoices, headers and lines. Every method joins the caller's transaction."""

import json
from dataclasses import asdict
from datetime import datetime
from typing import Any, Final

from sqlalchemy import Column, Row, Select, Subquery, func, literal, select, tuple_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.ingestion.application.records import (
    ClaimedJob,
    DuplicateContentError,
    EarlierCopy,
    EarlierInvoice,
    EntityCheckRecord,
    EntityResolutionRecord,
    EntityResolutionView,
    ExportInvoice,
    ExportLine,
    InvoiceHeaderView,
    InvoiceState,
    InvoiceView,
    JobLine,
    JobSummary,
    NewInvoice,
    QueuedInvoice,
)
from sextante.ingestion.domain.line_type import LineType, classify_line_type
from sextante.ingestion.domain.model import (
    BilledEntityBlock,
    ExtractedInvoice,
    ExtractedLine,
    StoredInvoice,
    StoredLine,
)
from sextante.ingestion.domain.normalization import normalize_extraction
from sextante.ingestion.domain.statuses import CLAIMED_JOB_STATUSES, InvoiceStatus, JobStatus
from sextante.ingestion.infrastructure.tables import (
    ENTITY_RESOLUTION_TABLE,
    INVOICE_HEADER_TABLE,
    INVOICE_LINE_TABLE,
    INVOICE_TABLE,
    JOB_TABLE,
)
from sextante.platform.insert_if_absent import insert_if_absent
from sextante.platform.supplier_key import supplier_key
from sextante.platform.text_normalization import normalize_for_comparison


class IngestionRepository:
    """Implements IngestionRepositoryPort, JobLinesReader and InvoiceExportReader.

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

    async def change_job_status(
        self, connection: AsyncConnection, job_id: str, current: JobStatus, new: JobStatus
    ) -> bool:
        """Move a job from ``current`` to ``new``; False when it was no longer ``current``.

        Conditional, so a job a reprocessing queued again is never moved back.

        Example:
            await repository.change_job_status(connection, job_id, RUNNING, WAITING_MODEL)
        """
        result = await connection.execute(
            update(JOB_TABLE)
            .where(JOB_TABLE.c.id == job_id, JOB_TABLE.c.status == current)
            .values(status=new)
        )
        return result.rowcount == 1

    async def finish_job(
        self, connection: AsyncConnection, job_id: str, status: JobStatus, now: datetime
    ) -> bool:
        """Close a claimed job; False when it was queued again meanwhile.

        A job queued again while it ran keeps its queued status, so the worker claims it
        again and codes the invoice that was queued after the list was read.

        Example:
            await repository.finish_job(connection, job_id, JobStatus.COMPLETED, now)
        """
        result = await connection.execute(
            update(JOB_TABLE)
            .where(JOB_TABLE.c.id == job_id, JOB_TABLE.c.status.in_(CLAIMED_JOB_STATUSES))
            .values(status=status, finished_at=now.isoformat())
        )
        return result.rowcount == 1

    async def requeue_interrupted_jobs(self, connection: AsyncConnection) -> int:
        """Queue again the jobs a stopped process left claimed; return how many.

        There is one worker, in the one process (D-3.4), so a claimed job at startup was
        interrupted: its invoices still queued are coded when it is claimed again.

        Example:
            await repository.requeue_interrupted_jobs(connection)  # 1
        """
        result = await connection.execute(
            update(JOB_TABLE)
            .where(JOB_TABLE.c.status.in_(CLAIMED_JOB_STATUSES))
            .values(status=JobStatus.QUEUED)
        )
        return result.rowcount

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
        return _stored_invoice(invoice_id, normalized, line_ids)

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
        ids_query = select(INVOICE_TABLE.c.id).where(INVOICE_TABLE.c.job_id == job_id)
        invoice_ids = tuple(str(i) for i in (await connection.execute(ids_query)).scalars())
        return JobSummary(job_id, str(status), counts, invoice_ids)

    async def read_job_lines(
        self, connection: AsyncConnection, job_id: str, invoice_id: str | None
    ) -> list[JobLine]:
        """Return the job's lines, or one invoice's, by upload order then document position."""
        rows = (await connection.execute(_job_lines_query(job_id, invoice_id))).all()
        return [
            JobLine(
                line_id=str(r.id),
                invoice_id=str(r.invoice_id),
                invoice_number=r.invoice_number,
                position=int(r.position),
                description=str(r.description),
                billed_entity=_detected_entity(_blocks(r.billed_entities)),
                entity_verdict=r.entity_verdict,
                entity_reason=r.entity_reason,
                possible_duplicate_of=r.possible_duplicate_of,
            )
            for r in rows
        ]

    async def line_belongs_to_invoice(
        self, connection: AsyncConnection, invoice_id: str, line_id: str
    ) -> bool:
        """True when the invoice line exists and is a line of this invoice."""
        table = INVOICE_LINE_TABLE
        query = select(table.c.id).where(table.c.id == line_id, table.c.invoice_id == invoice_id)
        return (await connection.execute(query)).first() is not None

    async def invoice_state(
        self, connection: AsyncConnection, invoice_id: str
    ) -> InvoiceState | None:
        """Return the invoice's job, status and entity verdict, or None when unknown."""
        header = INVOICE_HEADER_TABLE
        query = (
            select(
                INVOICE_TABLE.c.job_id,
                INVOICE_TABLE.c.status,
                header.c.entity_verdict,
                header.c.entity_reason,
            )
            .outerjoin(header, header.c.invoice_id == INVOICE_TABLE.c.id)
            .where(INVOICE_TABLE.c.id == invoice_id)
        )
        row = (await connection.execute(query)).first()
        if row is None:
            return None
        status = InvoiceStatus(str(row.status))
        return InvoiceState(str(row.job_id), status, row.entity_verdict, row.entity_reason)

    async def read_invoice_view(
        self, connection: AsyncConnection, invoice_id: str
    ) -> InvoiceView | None:
        """Return the invoice's state, header, resolution and earlier copy, or None."""
        row = (await connection.execute(_invoice_view_query(invoice_id))).first()
        return None if row is None else _invoice_view(invoice_id, row)

    async def record_entity_resolution(
        self, connection: AsyncConnection, invoice_id: str, resolution: EntityResolutionRecord
    ) -> bool:
        """Store the resolution; False when the invoice already had one (REQ-REV-006)."""
        values = {
            "invoice_id": invoice_id,
            "verdict": resolution.verdict,
            "note": resolution.note,
            "resolved_by": resolution.resolved_by,
            "resolved_at": resolution.resolved_at.isoformat(),
        }
        return await insert_if_absent(connection, ENTITY_RESOLUTION_TABLE, values, ("invoice_id",))

    async def entity_resolution(self, connection: AsyncConnection, invoice_id: str) -> str | None:
        """Return the verdict a reviewer chose for this invoice, or None."""
        table = ENTITY_RESOLUTION_TABLE
        query = select(table.c.verdict).where(table.c.invoice_id == invoice_id)
        verdict = (await connection.execute(query)).scalar_one_or_none()
        return str(verdict) if verdict is not None else None

    async def earlier_invoice_with_same_number(
        self, connection: AsyncConnection, invoice_id: str
    ) -> str | None:
        """Return the first invoice uploaded before this one with its supplier and number.

        An invoice without number, or without supplier, never matches (REQ-ING-011).
        """
        rows = (await connection.execute(_same_number_query(invoice_id))).all()
        return str(rows[0][0]) if rows else None

    async def record_possible_duplicate(
        self, connection: AsyncConnection, invoice_id: str, earlier_invoice_id: str
    ) -> bool:
        """Point the invoice at the earlier one; False when it already pointed there."""
        header = INVOICE_HEADER_TABLE
        result = await connection.execute(
            update(header)
            .where(header.c.invoice_id == invoice_id, header.c.possible_duplicate_of.is_(None))
            .values(possible_duplicate_of=earlier_invoice_id)
        )
        return result.rowcount == 1

    async def requeue_invoice(
        self, connection: AsyncConnection, invoice_id: str, job_id: str
    ) -> None:
        """Queue the invoice again and reopen its job, so the worker claims it (NFR-REL-001)."""
        await connection.execute(
            update(INVOICE_TABLE)
            .where(INVOICE_TABLE.c.id == invoice_id)
            .values(status=InvoiceStatus.QUEUED, status_reason=None)
        )
        await connection.execute(
            update(JOB_TABLE)
            .where(JOB_TABLE.c.id == job_id)
            .values(status=JobStatus.QUEUED, finished_at=None)
        )

    async def load_stored_invoice(
        self, connection: AsyncConnection, invoice_id: str
    ) -> StoredInvoice | None:
        """Rebuild the stored extraction from header and lines, for coding without extraction."""
        header_query = select(INVOICE_HEADER_TABLE).where(
            INVOICE_HEADER_TABLE.c.invoice_id == invoice_id
        )
        header = (await connection.execute(header_query)).first()
        if header is None:
            return None
        lines = await _stored_lines(connection, invoice_id)
        blocks = tuple(_blocks(header.billed_entities))
        return StoredInvoice(invoice_id, header.supplier_name, header.currency, blocks, lines)

    async def read_job_invoices(
        self, connection: AsyncConnection, job_id: str
    ) -> list[ExportInvoice]:
        """Return the job's invoices in upload order, each with its lines in document order."""
        invoices = (await connection.execute(_job_invoices_query(job_id))).all()
        lines = await _lines_by_invoice(connection, [str(row.id) for row in invoices])
        return [_export_invoice(row, lines.get(str(row.id), ())) for row in invoices]


def _supplier_and_number_of(invoice_id: str) -> Subquery:
    header, uploaded = INVOICE_HEADER_TABLE, INVOICE_TABLE.alias("uploaded")
    return (
        select(header.c.supplier_key, header.c.invoice_number, uploaded.c.created_at)
        .join(uploaded, uploaded.c.id == header.c.invoice_id)
        .where(header.c.invoice_id == invoice_id, func.trim(header.c.invoice_number) != "")
        .subquery()
    )


def _same_number_query(invoice_id: str) -> Select[tuple[object, ...]]:
    # Only an invoice uploaded before this one counts, so two copies never point at
    # each other; the non-unique index on (supplier_key, invoice_number) serves the join.
    earlier = INVOICE_HEADER_TABLE.alias("earlier")
    this = _supplier_and_number_of(invoice_id)
    same_invoice = (earlier.c.supplier_key == this.c.supplier_key) & (
        earlier.c.invoice_number == this.c.invoice_number
    )
    before = tuple_(INVOICE_TABLE.c.created_at, INVOICE_TABLE.c.id) < tuple_(
        this.c.created_at, literal(invoice_id)
    )
    return (
        select(earlier.c.invoice_id)
        .join(this, same_invoice)
        .join(INVOICE_TABLE, INVOICE_TABLE.c.id == earlier.c.invoice_id)
        .where(before)
        .order_by(INVOICE_TABLE.c.created_at, INVOICE_TABLE.c.id)
        .limit(1)
    )


def _invoice_view_query(invoice_id: str) -> Select[tuple[object, ...]]:
    # An explicit projection: storage name, digest and file name never leave (SEC-18).
    header, resolution = INVOICE_HEADER_TABLE, ENTITY_RESOLUTION_TABLE
    earlier = INVOICE_HEADER_TABLE.alias("earlier_header")
    return (
        select(
            INVOICE_TABLE.c.job_id,
            INVOICE_TABLE.c.status,
            INVOICE_TABLE.c.status_reason,
            *_header_columns(),
            earlier.c.invoice_number.label("earlier_number"),
            resolution.c.verdict.label("resolution_verdict"),
            resolution.c.note.label("resolution_note"),
            resolution.c.resolved_at,
        )
        .select_from(INVOICE_TABLE)
        .outerjoin(header, header.c.invoice_id == INVOICE_TABLE.c.id)
        .outerjoin(earlier, earlier.c.invoice_id == header.c.possible_duplicate_of)
        .outerjoin(resolution, resolution.c.invoice_id == INVOICE_TABLE.c.id)
        .where(INVOICE_TABLE.c.id == invoice_id)
    )


def _header_columns() -> tuple[Column[Any], ...]:
    columns = INVOICE_HEADER_TABLE.c
    names = (
        "supplier_name supplier_nif invoice_number invoice_date currency billed_entities "
        "target_sheet entity_verdict entity_reason possible_duplicate_of"
    ).split()
    return tuple(columns[name] for name in names)


def _invoice_view(invoice_id: str, row: Row[tuple[object, ...]]) -> InvoiceView:
    state = InvoiceState(
        str(row.job_id), InvoiceStatus(str(row.status)), row.entity_verdict, row.entity_reason
    )
    return InvoiceView(
        invoice_id, state, row.status_reason, _header_view(row), _resolution(row), _earlier(row)
    )


def _header_view(row: Row[tuple[object, ...]]) -> InvoiceHeaderView:
    return InvoiceHeaderView(
        supplier_name=row.supplier_name,
        supplier_nif=row.supplier_nif,
        invoice_number=row.invoice_number,
        invoice_date=row.invoice_date,
        currency=row.currency,
        billed_entity_detected=_detected_entity(_blocks(row.billed_entities)),
        target_sheet=row.target_sheet,
    )


def _resolution(row: Row[tuple[object, ...]]) -> EntityResolutionView | None:
    if row.resolution_verdict is None:
        return None
    return EntityResolutionView(
        str(row.resolution_verdict), str(row.resolution_note), str(row.resolved_at)
    )


def _earlier(row: Row[tuple[object, ...]]) -> EarlierInvoice | None:
    if row.possible_duplicate_of is None:
        return None
    return EarlierInvoice(str(row.possible_duplicate_of), row.earlier_number)


def _job_lines_query(job_id: str, invoice_id: str | None) -> Select[tuple[object, ...]]:
    lines, header = INVOICE_LINE_TABLE, INVOICE_HEADER_TABLE
    query = (
        select(
            lines.c.id,
            lines.c.invoice_id,
            header.c.invoice_number,
            lines.c.position,
            lines.c.description,
            header.c.billed_entities,
            header.c.entity_verdict,
            header.c.entity_reason,
            header.c.possible_duplicate_of,
        )
        .join(INVOICE_TABLE, INVOICE_TABLE.c.id == lines.c.invoice_id)
        .join(header, header.c.invoice_id == lines.c.invoice_id)
        .where(INVOICE_TABLE.c.job_id == job_id)
        .order_by(INVOICE_TABLE.c.created_at, INVOICE_TABLE.c.id, lines.c.position)
    )
    return query if invoice_id is None else query.where(lines.c.invoice_id == invoice_id)


def _stored_invoice(
    invoice_id: str, normalized: ExtractedInvoice, line_ids: list[str]
) -> StoredInvoice:
    return StoredInvoice(
        invoice_id=invoice_id,
        supplier_name=normalized.supplier.name,
        currency=normalized.currency,
        billed_entities=normalized.billed_entities,
        lines=tuple(
            StoredLine(
                line_id, line.position, line.description, classify_line_type(line.description)
            )
            for line_id, line in zip(line_ids, normalized.lines, strict=True)
        ),
    )


async def _stored_lines(connection: AsyncConnection, invoice_id: str) -> tuple[StoredLine, ...]:
    query = (
        select(INVOICE_LINE_TABLE)
        .where(INVOICE_LINE_TABLE.c.invoice_id == invoice_id)
        .order_by(INVOICE_LINE_TABLE.c.position)
    )
    return tuple(
        StoredLine(str(r.id), int(r.position), str(r.description), LineType(str(r.line_type)))
        for r in (await connection.execute(query)).all()
    )


# What the export reads of each invoice header (REQ-EXP-004, REQ-ENT-006).
EXPORT_HEADER_COLUMNS: Final = (
    "supplier_name",
    "supplier_nif",
    "invoice_number",
    "billed_entities",
    "entity_verdict",
    "entity_reason",
)


def _job_invoices_query(job_id: str) -> Select[tuple[object, ...]]:
    header, earlier = INVOICE_HEADER_TABLE, INVOICE_TABLE.alias("earlier")
    invoice = INVOICE_TABLE.c
    return (
        select(
            *(invoice.id, invoice.status, invoice.status_reason, invoice.content_digest),
            *(header.c[name] for name in EXPORT_HEADER_COLUMNS),
            earlier.c.display_name.label("earlier_file_name"),
            earlier.c.created_at.label("earlier_uploaded_at"),
        )
        .select_from(INVOICE_TABLE)
        .outerjoin(header, header.c.invoice_id == INVOICE_TABLE.c.id)
        .outerjoin(earlier, earlier.c.id == header.c.possible_duplicate_of)
        .where(INVOICE_TABLE.c.job_id == job_id)
        .order_by(INVOICE_TABLE.c.created_at, INVOICE_TABLE.c.id)
    )


async def _lines_by_invoice(
    connection: AsyncConnection, invoice_ids: list[str]
) -> dict[str, tuple[ExportLine, ...]]:
    table = INVOICE_LINE_TABLE
    query = (
        select(table.c.invoice_id, table.c.id, table.c.position, table.c.description)
        .where(table.c.invoice_id.in_(invoice_ids))
        .order_by(table.c.invoice_id, table.c.position)
    )
    grouped: dict[str, list[ExportLine]] = {}
    for row in (await connection.execute(query)).all():
        line = ExportLine(str(row.id), int(row.position), str(row.description))
        grouped.setdefault(str(row.invoice_id), []).append(line)
    return {invoice_id: tuple(lines) for invoice_id, lines in grouped.items()}


def _export_invoice(row: Row[tuple[object, ...]], lines: tuple[ExportLine, ...]) -> ExportInvoice:
    blocks = _blocks(row.billed_entities)
    return ExportInvoice(
        invoice_id=str(row.id),
        status=InvoiceStatus(str(row.status)),
        status_reason=row.status_reason,
        content_digest=str(row.content_digest),
        supplier_name=row.supplier_name,
        supplier_nif=row.supplier_nif,
        invoice_number=row.invoice_number,
        billed_entity=_detected_entity(blocks),
        care_of=tuple(text for block in blocks for text in block.care_of),
        entity_verdict=row.entity_verdict,
        lines=lines,
        entity_reason=row.entity_reason,
        earlier_copy=_earlier_copy(row),
    )


def _earlier_copy(row: Row[tuple[object, ...]]) -> EarlierCopy | None:
    if row.earlier_file_name is None:
        return None
    uploaded_at = datetime.fromisoformat(str(row.earlier_uploaded_at))
    return EarlierCopy(str(row.earlier_file_name), uploaded_at)


def _blocks(billed_entities_json: object) -> list[BilledEntityBlock]:
    # Parsed once, into the domain type, from the JSON column written by store_extraction.
    if not billed_entities_json:
        return []
    return [
        BilledEntityBlock(
            name=block["name"],
            nif=block["nif"],
            care_of=tuple(block["care_of"]),
            address_lines=tuple(block["address_lines"]),
        )
        for block in json.loads(str(billed_entities_json))
    ]


def _detected_entity(blocks: list[BilledEntityBlock]) -> str | None:
    # The billed entity as extracted, never normalized for comparison (REQ-ENT-006).
    # Several blocks are shown together, so a reviewer sees why the entity is ambiguous.
    return " | ".join(block.name for block in blocks) if blocks else None


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
        "supplier_key": supplier_key(extraction.supplier.nif, extraction.supplier.name),
    }


def _line_row(invoice_id: str, line_id: str, line: ExtractedLine) -> dict[str, object]:
    return {
        "id": line_id,
        "invoice_id": invoice_id,
        "position": line.position,
        "description": line.description,
        "normalized_description": normalize_for_comparison(line.description),
        "line_type": classify_line_type(line.description).value,
        # Decimals are stored as text: SQLite has no exact decimal type (D-3.5).
        "quantity": _decimal_text(line.quantity),
        "unit_price": _decimal_text(line.unit_price),
        "vat_rate": _decimal_text(line.vat_rate),
        "amount": _decimal_text(line.amount),
    }


def _decimal_text(value: object) -> str | None:
    return None if value is None else str(value)
