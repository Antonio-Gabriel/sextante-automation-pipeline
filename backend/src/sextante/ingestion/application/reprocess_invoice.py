"""Queue a failed invoice again, to be coded from its stored text (NFR-REL-001, NFR-REL-002)."""

from dataclasses import dataclass
from typing import Final

from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.ingestion.application.ports import ReprocessingRepositoryPort
from sextante.ingestion.domain.statuses import InvoiceStatus
from sextante.platform.audit import AuditEventRepository
from sextante.platform.clock import Clock, IdentifierGenerator
from sextante.platform.errors import DomainError

# A failed invoice is coded for the first time; a coded one again, its earlier coding
# kept as superseded (NFR-REL-002, D-3.23).
REPROCESSABLE_STATUSES: Final = frozenset({InvoiceStatus.FAILED, InvoiceStatus.ENCODED})


class InvoiceNotFoundError(DomainError):
    """No invoice has this identifier."""

    user_message_key = "errors.invoice.not_found"


class InvoiceNotReprocessableError(DomainError):
    """Only a failed or a coded invoice is reprocessed (NFR-REL-002, ticket 14).

    A refused document has no text to code, and an ambiguous one waits for its entity
    to be resolved (REQ-REV-006).
    """

    user_message_key = "errors.invoice.not_reprocessable"


@dataclass(frozen=True, slots=True)
class ReprocessReceipt:
    """The invoice and the job that will code it again."""

    invoice_id: str
    job_id: str


class ReprocessInvoice:
    """Put a failed invoice back in its job's queue. Asking twice queues it once.

    Example:
        receipt = await ReprocessInvoice(repository, audit, clock, ids).execute(conn, invoice_id)
    """

    def __init__(
        self,
        repository: ReprocessingRepositoryPort,
        audit: AuditEventRepository,
        clock: Clock,
        identifiers: IdentifierGenerator,
    ) -> None:
        self._repository = repository
        self._audit = audit
        self._clock = clock
        self._identifiers = identifiers

    async def execute(self, connection: AsyncConnection, invoice_id: str) -> ReprocessReceipt:
        """Queue the invoice again; an invoice already queued is left as it is.

        Runs in the caller's transaction, the one that records the Idempotency-Key (SEC-19).

        Example:
            (await reprocess.execute(connection, "3f2a...")).job_id

        Raises:
            InvoiceNotFoundError: when no invoice has this identifier.
            InvoiceNotReprocessableError: when the invoice did not fail.
        """
        state = await self._repository.invoice_state(connection, invoice_id)
        if state is None:
            raise InvoiceNotFoundError(f"Invoice {invoice_id!r} does not exist.")
        if state.status in REPROCESSABLE_STATUSES:
            await self._repository.requeue_invoice(connection, invoice_id, state.job_id)
            await self._audit.append(
                connection,
                self._identifiers.new_id(),
                "invoice_reprocess_requested",
                ("invoice", invoice_id),
                {"job_id": state.job_id, "previous_status": state.status.value},
                self._clock.now(),
            )
        elif state.status is not InvoiceStatus.QUEUED:
            raise InvoiceNotReprocessableError(
                f"Invoice {invoice_id!r} is {state.status.value}. Expected a failed or coded "
                "invoice."
            )
        return ReprocessReceipt(invoice_id, state.job_id)
