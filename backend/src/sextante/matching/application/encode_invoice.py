"""Code and store the lines of one routed invoice (REQ-MAP-004 to REQ-MAP-009, SEC-14).

LineCoder decides; this use case stores the decisions, the model call and the audit
events in one transaction.
"""

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from sextante.catalog.contracts import Catalog, TargetSheet
from sextante.ingestion.contracts import StoredInvoice, StoredLine
from sextante.matching.application.line_coding import LineCoder, LineOutcome, with_flags
from sextante.matching.application.ports import MatchingRepositoryPort
from sextante.matching.application.records import (
    CodingsSummary,
    EncodedLineRecord,
    ModelCallRecord,
)
from sextante.matching.domain.line_decision import FlagReason, uncoded_line_decision
from sextante.platform.audit import AuditEventRepository
from sextante.platform.clock import Clock, IdentifierGenerator
from sextante.platform.text_normalization import normalize_for_comparison

# Writes another module makes in the same transaction as the line records, so that the
# entity verdict and the lines it produced are stored together or not at all.
SameTransactionWrite = Callable[[AsyncConnection], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class EncodingCollaborators:
    """Everything EncodeInvoice needs, injected (04-padroes-de-codigo.md §4)."""

    engine: AsyncEngine
    coder: LineCoder
    catalog: Catalog
    repository: MatchingRepositoryPort
    audit: AuditEventRepository
    clock: Clock
    identifiers: IdentifierGenerator


class EncodeInvoice:
    """One model call per invoice, then every answer validated, decided and audited.

    Example:
        await EncodeInvoice(collaborators).execute(stored_invoice, TargetSheet.OUTLAYS, write)
    """

    def __init__(self, collaborators: EncodingCollaborators) -> None:
        self._collaborators = collaborators

    async def execute(
        self,
        invoice: StoredInvoice,
        target_sheet: TargetSheet,
        also_write: SameTransactionWrite,
        invoice_flags: tuple[FlagReason, ...] = (),
        line_flags: Mapping[str, tuple[FlagReason, ...]] = MappingProxyType({}),
    ) -> None:
        """Code the service lines with one model call; record VAT and discount lines as such.

        ``invoice_flags`` concern the whole invoice, such as a possible duplicate, and are
        added to every line, sending it to review (REQ-ING-011). ``line_flags`` go on the
        lines they name, such as a review the new coding supersedes (D-3.23).

        Example:
            await encoder.execute(stored_invoice, TargetSheet.OUTLAYS, record_header)
        """
        deps = self._collaborators
        coded = await deps.coder.code(invoice, target_sheet, invoice_flags, line_flags)
        call = (
            ModelCallRecord(
                deps.identifiers.new_id(), invoice.invoice_id, coded.response, deps.clock.now()
            )
            if coded.response is not None
            else None
        )
        await self._persist(
            invoice.invoice_id, list(coded.outcomes), target_sheet, call, also_write
        )

    async def record_uncoded(
        self,
        invoice: StoredInvoice,
        reason: FlagReason,
        also_write: SameTransactionWrite,
        invoice_flags: tuple[FlagReason, ...] = (),
    ) -> None:
        """Record every line of an ambiguous invoice: no sheet, no code, LOW, flagged (D-3.15).

        Example:
            await encoder.record_uncoded(stored_invoice, FlagReason.ENTITY_NIF_MISMATCH, write)
        """
        decision = uncoded_line_decision(reason)
        outcomes = [LineOutcome(line, None, decision, ()) for line in invoice.lines]
        await self._persist(
            invoice.invoice_id,
            [with_flags(o, invoice_flags) for o in outcomes],
            None,
            None,
            also_write,
        )

    async def _persist(
        self,
        invoice_id: str,
        outcomes: list[LineOutcome],
        target_sheet: TargetSheet | None,
        call: ModelCallRecord | None,
        also_write: SameTransactionWrite,
    ) -> None:
        deps = self._collaborators
        async with deps.engine.begin() as connection:
            await also_write(connection)
            # A line coded again, after an entity resolution, keeps its earlier coding as
            # superseded: the new one takes over without overwriting it (REQ-REV-004).
            line_ids = [outcome.line.line_id for outcome in outcomes]
            earlier = await deps.repository.codings_in_force(connection, line_ids)
            await deps.repository.supersede_codings(connection, line_ids, deps.clock.now())
            if call is not None:
                await deps.repository.record_model_call(connection, call)
            for outcome in outcomes:
                await self._persist_line(connection, outcome, target_sheet, call)
            if earlier.line_count:
                await self._audit_recoding(connection, invoice_id, earlier, outcomes, call)

    async def _audit_recoding(
        self,
        connection: AsyncConnection,
        invoice_id: str,
        earlier: CodingsSummary,
        outcomes: list[LineOutcome],
        call: ModelCallRecord | None,
    ) -> None:
        # What coded the invoice before and what codes it now (NFR-REL-002, ticket 14).
        deps = self._collaborators
        flagged_again = sum(1 for o in outcomes if FlagReason.REVIEW_SUPERSEDED in o.decision.flags)
        payload = {
            "previous_prompt_versions": list(earlier.prompt_versions),
            "previous_catalog_digests": list(earlier.catalog_digests),
            "new_prompt_version": call.response.prompt_version if call else None,
            "new_catalog_digest": str(deps.catalog.digest),
            "superseded_lines": earlier.line_count,
            "reviews_flagged_again": flagged_again,
        }
        await deps.audit.append(
            connection,
            deps.identifiers.new_id(),
            "invoice_recoded",
            ("invoice", invoice_id),
            payload,
            deps.clock.now(),
        )

    async def _persist_line(
        self,
        connection: AsyncConnection,
        outcome: LineOutcome,
        target_sheet: TargetSheet | None,
        call: ModelCallRecord | None,
    ) -> None:
        deps = self._collaborators
        record = self._record_for(outcome, target_sheet, call)
        await deps.repository.record_encoded_line(connection, record)
        await deps.audit.append(
            connection,
            deps.identifiers.new_id(),
            "line_encoded" if target_sheet else "line_not_coded",
            ("invoice_line", outcome.line.line_id),
            _audit_payload(outcome.line, record, call),
            record.encoded_at,
        )

    def _record_for(
        self, outcome: LineOutcome, target_sheet: TargetSheet | None, call: ModelCallRecord | None
    ) -> EncodedLineRecord:
        deps = self._collaborators
        return EncodedLineRecord(
            encoded_line_id=deps.identifiers.new_id(),
            invoice_line_id=outcome.line.line_id,
            target_sheet=target_sheet,
            choice=outcome.choice,
            decision=outcome.decision,
            scores=outcome.scores,
            catalog_digest=str(deps.catalog.digest),
            model_call_id=call.call_id if call else None,
            encoded_at=deps.clock.now(),
        )


def _audit_payload(
    line: StoredLine, record: EncodedLineRecord, call: ModelCallRecord | None
) -> dict[str, object]:
    # The audit trail lives in the database, with its own access and retention, so it
    # keeps the description that fed the decision; the log does not (REQ-AUD-001, SEC-15).
    catalog_item = record.decision.catalog_item
    return {
        "description": line.description,
        "normalized_description": normalize_for_comparison(line.description),
        "target_sheet": record.target_sheet.value if record.target_sheet else None,
        "choice_outcome": record.choice.outcome.value if record.choice else "not_coded",
        "candidate_index": record.choice.candidate_index if record.choice else None,
        "item_number": catalog_item.item_number.value if catalog_item else None,
        "confidence": record.decision.confidence.value,
        "confidence_rule": record.decision.rule,
        "flags": [flag.value for flag in record.decision.flags],
        "scores": [[score.item_number, score.score] for score in record.scores],
        "model_id": call.response.model_id if call else None,
        "prompt_version": call.response.prompt_version if call else None,
        "catalog_digest": record.catalog_digest,
        "encoded_at": record.encoded_at.isoformat(),
    }
