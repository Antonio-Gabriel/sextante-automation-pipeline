"""Queue a failed invoice again, to be coded from its stored text (NFR-REL-001, NFR-REL-002)."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine

from sextante.ingestion.application.ports import ReprocessingRepositoryPort
from sextante.ingestion.domain.statuses import InvoiceStatus
from sextante.platform.audit import AuditEventRepository
from sextante.platform.clock import Clock, IdentifierGenerator
from sextante.platform.errors import DomainError


class InvoiceNotFoundError(DomainError):
    """No invoice has this identifier."""

    user_message_key = "errors.invoice.not_found"


class InvoiceNotReprocessableError(DomainError):
    """Only a failed invoice is reprocessed: a coded one is never coded twice."""

    user_message_key = "errors.invoice.not_reprocessable"


@dataclass(frozen=True, slots=True)
class ReprocessReceipt:
    """The invoice and the job that will code it again."""

    invoice_id: str
    job_id: str


class ReprocessInvoice:
    """Put a failed invoice back in its job's queue. Asking twice queues it once.

    Example:
        receipt = await ReprocessInvoice(engine, repository, audit, clock, ids).execute(invoice_id)
    """

    def __init__(
        self,
        engine: AsyncEngine,
        repository: ReprocessingRepositoryPort,
        audit: AuditEventRepository,
        clock: Clock,
        identifiers: IdentifierGenerator,
    ) -> None:
        self._engine = engine
        self._repository = repository
        self._audit = audit
        self._clock = clock
        self._identifiers = identifiers

    async def execute(self, invoice_id: str) -> ReprocessReceipt:
        """Queue the invoice again; an invoice already queued is left as it is.

        Example:
            (await reprocess.execute("3f2a...")).job_id

        Raises:
            InvoiceNotFoundError: when no invoice has this identifier.
            InvoiceNotReprocessableError: when the invoice did not fail.
        """
        async with self._engine.begin() as connection:
            state = await self._repository.invoice_state(connection, invoice_id)
            if state is None:
                raise InvoiceNotFoundError(f"Invoice {invoice_id!r} does not exist.")
            if state.status is InvoiceStatus.FAILED:
                await self._repository.requeue_invoice(connection, invoice_id, state.job_id)
                await self._audit.append(
                    connection,
                    self._identifiers.new_id(),
                    "invoice_reprocess_requested",
                    ("invoice", invoice_id),
                    {"job_id": state.job_id},
                    self._clock.now(),
                )
            elif state.status is not InvoiceStatus.QUEUED:
                raise InvoiceNotReprocessableError(
                    f"Invoice {invoice_id!r} is {state.status.value}. Expected a failed invoice."
                )
        return ReprocessReceipt(invoice_id, state.job_id)
