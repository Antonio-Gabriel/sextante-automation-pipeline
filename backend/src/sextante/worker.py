"""In-process worker: claims queued jobs and codes their invoices (D-3.4)."""

import asyncio
import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine

from sextante.catalog.contracts import TargetSheet
from sextante.ingestion.application.ports import IngestionRepositoryPort
from sextante.ingestion.application.records import ClaimedJob, QueuedInvoice
from sextante.ingestion.contracts import (
    ExtractionRejection,
    FileFormat,
    InvoiceExtractor,
    StoredInvoice,
)
from sextante.ingestion.domain.ports import InvoiceFileStore
from sextante.ingestion.domain.statuses import InvoiceStatus, JobStatus
from sextante.matching.application.encode_invoice import EncodeInvoice
from sextante.matching.domain.routing import route_invoice
from sextante.platform.clock import Clock, IdentifierGenerator
from sextante.platform.structured_logging import correlation_id_var

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class WorkerCollaborators:
    """Everything the worker needs, injected (04-padroes-de-codigo.md §4)."""

    engine: AsyncEngine
    repository: IngestionRepositoryPort
    store: InvoiceFileStore
    extractor: InvoiceExtractor
    encoder: EncodeInvoice
    clock: Clock
    identifiers: IdentifierGenerator
    target_entity_name: str
    poll_seconds: float


class EncodingWorker:
    """Poll for queued jobs, claim one atomically, and code its invoices one by one.

    Example:
        task = asyncio.create_task(EncodingWorker(collaborators).run_forever())
    """

    def __init__(self, collaborators: WorkerCollaborators) -> None:
        self._with = collaborators
        self._worker_id = collaborators.identifiers.new_id()

    async def run_forever(self) -> None:
        """Process jobs until cancelled at shutdown."""
        while True:
            if not await self.process_next_job():
                await asyncio.sleep(self._with.poll_seconds)

    async def process_next_job(self) -> bool:
        """Claim and process one job. Return False when no job was waiting."""
        async with self._with.engine.begin() as connection:
            job = await self._with.repository.claim_next_job(
                connection, self._worker_id, self._with.clock.now()
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
        async with self._with.engine.connect() as connection:
            invoices = await self._with.repository.queued_invoices(connection, job.job_id)
        for invoice in invoices:
            await self._process_invoice_isolated(invoice)
        async with self._with.engine.begin() as connection:
            await self._with.repository.finish_job(
                connection, job.job_id, JobStatus.COMPLETED, self._with.clock.now()
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
        async with self._with.engine.begin() as connection:
            await self._with.repository.set_invoice_status(
                connection, invoice.invoice_id, status, reason
            )

    async def _process_invoice(self, invoice: QueuedInvoice) -> tuple[InvoiceStatus, str | None]:
        content = self._with.store.read(invoice.storage_name)
        extraction = self._with.extractor.extract(content, FileFormat(invoice.file_format))
        if isinstance(extraction, ExtractionRejection):
            return InvoiceStatus.REJECTED, extraction.reason.value
        async with self._with.engine.begin() as connection:
            line_ids = [self._with.identifiers.new_id() for _ in extraction.lines]
            stored = await self._with.repository.store_extraction(
                connection, invoice.invoice_id, extraction, line_ids
            )
        return await self._encode(stored)

    async def _encode(self, stored: StoredInvoice) -> tuple[InvoiceStatus, str | None]:
        target_sheet = route_invoice(stored.billed_entities, self._with.target_entity_name)
        if target_sheet is None:
            return InvoiceStatus.NOT_CODED, "entity_not_resolved"
        async with self._with.engine.begin() as connection:
            await self._with.repository.set_target_sheet(
                connection, stored.invoice_id, target_sheet.value
            )
        await self._with.encoder.execute(stored, TargetSheet(target_sheet))
        logger.info(
            "invoice_encoded",
            extra={"invoice_id": stored.invoice_id, "line_count": len(stored.lines)},
        )
        return InvoiceStatus.ENCODED, None
