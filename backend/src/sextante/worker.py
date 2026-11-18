"""In-process worker: claims queued jobs and codes their invoices (D-3.4)."""

import asyncio
import logging
from collections.abc import Mapping
from dataclasses import asdict, dataclass

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from sextante.catalog.contracts import TargetSheet
from sextante.ingestion.application.ports import IngestionRepositoryPort
from sextante.ingestion.application.records import ClaimedJob, EntityCheckRecord, QueuedInvoice
from sextante.ingestion.contracts import (
    ExtractedInvoice,
    ExtractionRejection,
    FileFormat,
    InvoiceExtractor,
    StoredInvoice,
    missing_fields,
)
from sextante.ingestion.domain.ports import InvoiceFileStore
from sextante.ingestion.domain.statuses import InvoiceStatus, JobStatus
from sextante.matching.application.encode_invoice import EncodeInvoice, SameTransactionWrite
from sextante.matching.contracts import (
    REVIEWER_RESOLUTION_REASON,
    EntityCheckResult,
    EntityDenylist,
    EntityVerdict,
    FlagReason,
    TargetEntity,
    check_billed_entity,
    target_sheet_for,
)
from sextante.platform.audit import AuditEventRepository
from sextante.platform.clock import Clock, IdentifierGenerator
from sextante.platform.structured_logging import correlation_id_var
from sextante.review.contracts import CodingsInForce

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class WorkerCollaborators:
    """Everything the worker needs, injected (04-padroes-de-codigo.md §4)."""

    engine: AsyncEngine
    repository: IngestionRepositoryPort
    store: InvoiceFileStore
    extractor: InvoiceExtractor
    encoder: EncodeInvoice
    audit: AuditEventRepository
    clock: Clock
    identifiers: IdentifierGenerator
    target_entity: TargetEntity
    denylist: EntityDenylist
    codings: CodingsInForce
    poll_seconds: float


class EncodingWorker:
    """Poll for queued jobs, claim one atomically, and code its invoices one by one.

    Example:
        task = asyncio.create_task(EncodingWorker(collaborators).run_forever())
    """

    def __init__(self, collaborators: WorkerCollaborators) -> None:
        self._collaborators = collaborators
        self._worker_id = collaborators.identifiers.new_id()

    async def run_forever(self) -> None:
        """Process jobs until cancelled at shutdown."""
        while True:
            if not await self.process_next_job():
                await asyncio.sleep(self._collaborators.poll_seconds)

    async def process_next_job(self) -> bool:
        """Claim and process one job. Return False when no job was waiting."""
        async with self._collaborators.engine.begin() as connection:
            job = await self._collaborators.repository.claim_next_job(
                connection, self._worker_id, self._collaborators.clock.now()
            )
        if job is None:
            return False
        token = correlation_id_var.set(job.correlation_id)
        try:
            await self._process_job(job)
        finally:
            correlation_id_var.reset(token)
        return True

    async def _process_job(self, job: ClaimedJob) -> None:
        async with self._collaborators.engine.connect() as connection:
            invoices = await self._collaborators.repository.queued_invoices(connection, job.job_id)
        for invoice in invoices:
            await self._process_invoice_isolated(invoice)
        async with self._collaborators.engine.begin() as connection:
            await self._collaborators.repository.finish_job(
                connection, job.job_id, JobStatus.COMPLETED, self._collaborators.clock.now()
            )
        logger.info("job_completed", extra={"job_id": job.job_id, "invoice_count": len(invoices)})

    async def _process_invoice_isolated(self, invoice: QueuedInvoice) -> None:
        # One invoice failing does not stop the job (REQ-PLT-002). The failure is recorded
        # on the invoice and logged with its type only, never swallowed.
        try:
            status, reason = await self._process_invoice(invoice)
        except Exception as error:
            status, reason = InvoiceStatus.FAILED, type(error).__name__
            logger.error(
                "invoice_failed", extra={"invoice_id": invoice.invoice_id, "error_type": reason}
            )
        async with self._collaborators.engine.begin() as connection:
            await self._collaborators.repository.set_invoice_status(
                connection, invoice.invoice_id, status, reason
            )

    async def _process_invoice(self, invoice: QueuedInvoice) -> tuple[InvoiceStatus, str | None]:
        # A reprocessed invoice is coded from its stored text, never extracted twice
        # (NFR-REL-002).
        async with self._collaborators.engine.connect() as connection:
            stored = await self._collaborators.repository.load_stored_invoice(
                connection, invoice.invoice_id
            )
        if stored is not None:
            return await self._encode(stored)
        content = self._collaborators.store.read(invoice.storage_name)
        extraction = self._collaborators.extractor.extract(content, FileFormat(invoice.file_format))
        if isinstance(extraction, ExtractionRejection):
            return InvoiceStatus.REJECTED, extraction.reason.value
        return await self._encode(await self._store(invoice.invoice_id, extraction))

    async def _store(self, invoice_id: str, extraction: ExtractedInvoice) -> StoredInvoice:
        deps = self._collaborators
        async with deps.engine.begin() as connection:
            line_ids = [deps.identifiers.new_id() for _ in extraction.lines]
            stored = await deps.repository.store_extraction(
                connection, invoice_id, extraction, line_ids
            )
            # Subtotal, VAT and total are not invoice lines: they are kept once, for the
            # invoice, in the audit trail (D-3.17, REQ-ING-006).
            await deps.audit.append(
                connection,
                deps.identifiers.new_id(),
                "summary_rows_extracted",
                ("invoice", invoice_id),
                {"summary_rows": [asdict(row) for row in extraction.summary_rows]},
                deps.clock.now(),
            )
            await self._audit_missing_fields(connection, invoice_id, extraction)
        return stored

    async def _audit_missing_fields(
        self, connection: AsyncConnection, invoice_id: str, extraction: ExtractedInvoice
    ) -> None:
        # A field the document did not show stays empty and is recorded as missing, by
        # name, with the invoice (REQ-ING-003).
        missing = missing_fields(extraction)
        if missing:
            deps = self._collaborators
            await deps.audit.append(
                connection,
                deps.identifiers.new_id(),
                "extraction_fields_missing",
                ("invoice", invoice_id),
                {"missing_fields": list(missing)},
                deps.clock.now(),
            )

    async def _encode(self, stored: StoredInvoice) -> tuple[InvoiceStatus, str | None]:
        deps = self._collaborators
        check, by_reviewer, earlier = await self._invoice_context(stored)
        target_sheet = target_sheet_for(check.verdict)
        # A possible duplicate is coded as usual, never blocked, and flagged (REQ-ING-011).
        flags = (FlagReason.POSSIBLE_DUPLICATE,) if earlier else ()
        record_header = self._header_writer(
            stored.invoice_id, _entity_record(check, target_sheet, by_reviewer), earlier
        )
        if target_sheet is None:
            # An ambiguous entity is never coded by guess: its lines are recorded LOW and
            # flagged with the reason, and a reviewer resolves the entity (D-3.15).
            reason = check.ambiguity_flag()
            await deps.encoder.record_uncoded(stored, reason, record_header, flags)
            return InvoiceStatus.NOT_CODED, reason.value
        reviewed = await self._reviewed_lines(stored)
        await deps.encoder.execute(stored, target_sheet, record_header, flags, reviewed)
        extra = {"invoice_id": stored.invoice_id, "line_count": len(stored.lines)}
        logger.info("invoice_encoded", extra=extra)
        return InvoiceStatus.ENCODED, None

    async def _reviewed_lines(self, stored: StoredInvoice) -> Mapping[str, tuple[FlagReason, ...]]:
        # A line a reviewer decided on goes back to review when it is coded again: the
        # earlier review stays with the earlier coding, never silently applied (D-3.23).
        deps = self._collaborators
        line_ids = [line.line_id for line in stored.lines]
        async with deps.engine.connect() as connection:
            codings = await deps.codings.read(connection, line_ids)
        return {
            line_id: (FlagReason.REVIEW_SUPERSEDED,)
            for line_id, coding in codings.items()
            if coding.reviewed
        }

    async def _invoice_context(
        self, stored: StoredInvoice
    ) -> tuple[EntityCheckResult, bool, str | None]:
        # A reviewer's resolution replaces the entity check, and is not limited by it: the
        # lines follow the normal confidence rule (REQ-REV-006, D-3.15).
        deps = self._collaborators
        invoice_id = stored.invoice_id
        async with deps.engine.connect() as connection:
            resolution = await deps.repository.entity_resolution(connection, invoice_id)
            earlier = await deps.repository.earlier_invoice_with_same_number(connection, invoice_id)
        if resolution is not None:
            return EntityCheckResult(EntityVerdict(resolution)), True, earlier
        check = check_billed_entity(stored.billed_entities, deps.target_entity, deps.denylist)
        return check, False, earlier

    def _header_writer(
        self, invoice_id: str, record: EntityCheckRecord, earlier_invoice_id: str | None
    ) -> SameTransactionWrite:
        # Run inside the transaction that stores the lines, so the verdict is never kept
        # without the lines it produced, nor the reverse.
        repository = self._collaborators.repository

        async def write(connection: AsyncConnection) -> None:
            await repository.record_entity_check(connection, invoice_id, record)
            # Audited once: coding the invoice again, after a resolution, finds it recorded.
            if earlier_invoice_id is not None and await repository.record_possible_duplicate(
                connection, invoice_id, earlier_invoice_id
            ):
                await self._audit_duplicate(connection, invoice_id, earlier_invoice_id)

        return write

    async def _audit_duplicate(
        self, connection: AsyncConnection, invoice_id: str, earlier_invoice_id: str
    ) -> None:
        deps = self._collaborators
        await deps.audit.append(
            connection,
            deps.identifiers.new_id(),
            "possible_duplicate_detected",
            ("invoice", invoice_id),
            {"earlier_invoice_id": earlier_invoice_id},
            deps.clock.now(),
        )


def _entity_record(
    check: EntityCheckResult, target_sheet: TargetSheet | None, by_reviewer: bool
) -> EntityCheckRecord:
    # A reviewer's verdict is stored with its own reason, so the output can tell it from
    # an exact match the check found (REQ-ENT-006).
    reason = check.reason.value if check.reason else None
    return EntityCheckRecord(
        verdict=check.verdict.value,
        reason=REVIEWER_RESOLUTION_REASON if by_reviewer else reason,
        target_sheet=target_sheet.value if target_sheet else None,
    )
