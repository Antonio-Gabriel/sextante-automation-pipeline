"""A reviewer resolves an ambiguous entity, and the invoice is queued for coding (REQ-REV-006).

The resolution is a human decision about one invoice. It never changes the denylist or
the configuration, which change only by an explicit decision (D-3.15).
"""

from dataclasses import dataclass
from typing import Final

from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.ingestion.application.ports import ReprocessingRepositoryPort
from sextante.ingestion.application.records import EntityResolutionRecord, InvoiceState
from sextante.ingestion.application.reprocess_invoice import (
    InvoiceNotFoundError,
    ReprocessReceipt,
)
from sextante.ingestion.domain.statuses import InvoiceStatus
from sextante.platform.audit import AuditEventRepository
from sextante.platform.clock import Clock, IdentifierGenerator
from sextante.platform.errors import DomainError

# The verdict the entity check left on an invoice it would not route (D-3.15).
AMBIGUOUS_VERDICT: Final = "AMBIGUOUS"


class InvoiceNotAmbiguousError(DomainError):
    """Only an invoice left ambiguous by the entity check, and not yet resolved, is resolved."""

    user_message_key = "errors.entity.not_ambiguous"


@dataclass(frozen=True, slots=True)
class ResolutionCollaborators:
    """Everything ResolveEntity needs, injected (04-padroes-de-codigo.md §4)."""

    repository: ReprocessingRepositoryPort
    audit: AuditEventRepository
    clock: Clock
    identifiers: IdentifierGenerator
    reviewer_id: str


class ResolveEntity:
    """Record the reviewer's verdict and put the invoice back in its job's queue.

    Example:
        receipt = await ResolveEntity(collaborators).execute(conn, invoice_id, "MATCH", note)
    """

    def __init__(self, collaborators: ResolutionCollaborators) -> None:
        self._deps = collaborators

    async def execute(
        self, connection: AsyncConnection, invoice_id: str, verdict: str, note: str
    ) -> ReprocessReceipt:
        """Resolve the entity as MATCH or NO_MATCH; the worker then codes the stored text.

        Runs in the caller's transaction, the one that records the Idempotency-Key (SEC-19).

        Example:
            await resolve.execute(connection, "3f2a...", "NO_MATCH", "Empresa irmã.")

        Raises:
            InvoiceNotFoundError: when no invoice has this identifier.
            InvoiceNotAmbiguousError: when the invoice is not ambiguous or already resolved.
        """
        deps = self._deps
        state = await deps.repository.invoice_state(connection, invoice_id)
        if state is None:
            raise InvoiceNotFoundError(f"Invoice {invoice_id!r} does not exist.")
        now = deps.clock.now()
        resolution = EntityResolutionRecord(verdict, note, deps.reviewer_id, now)
        await self._record_once(connection, invoice_id, state, resolution)
        await deps.repository.requeue_invoice(connection, invoice_id, state.job_id)
        await deps.audit.append(
            connection,
            deps.identifiers.new_id(),
            "entity_resolved",
            ("invoice", invoice_id),
            _audit_payload(state, resolution),
            now,
            author=deps.reviewer_id,
        )
        return ReprocessReceipt(invoice_id, state.job_id)

    async def _record_once(
        self,
        connection: AsyncConnection,
        invoice_id: str,
        state: InvoiceState,
        resolution: EntityResolutionRecord,
    ) -> None:
        ambiguous = (
            state.entity_verdict == AMBIGUOUS_VERDICT and state.status is InvoiceStatus.NOT_CODED
        )
        # The primary key on the resolution decides a race between two reviewers.
        if not ambiguous or not await self._deps.repository.record_entity_resolution(
            connection, invoice_id, resolution
        ):
            raise InvoiceNotAmbiguousError(
                f"Invoice {invoice_id!r} is not an unresolved ambiguous invoice. Expected "
                f"verdict {AMBIGUOUS_VERDICT}, found {state.entity_verdict}."
            )


def _audit_payload(state: InvoiceState, resolution: EntityResolutionRecord) -> dict[str, object]:
    # The previous and the new verdict, and why (REQ-REV-006, REQ-REV-004).
    return {
        "previous_verdict": state.entity_verdict,
        "previous_reason": state.entity_reason,
        "new_verdict": resolution.verdict,
        "note": resolution.note,
    }
