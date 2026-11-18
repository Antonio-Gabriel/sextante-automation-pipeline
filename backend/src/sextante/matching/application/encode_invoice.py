"""Code the service lines of one routed invoice (REQ-MAP-004 to REQ-MAP-009, SEC-14)."""

import dataclasses
import logging
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from sextante.catalog.contracts import Catalog, CatalogItem, ItemNumber, TargetSheet
from sextante.ingestion.contracts import LineType, StoredInvoice, StoredLine
from sextante.matching.application.ports import (
    ItemClassifier,
    ItemClassifierUnavailableError,
    LexicalScorer,
    MatchingRepositoryPort,
)
from sextante.matching.application.records import EncodedLineRecord, ModelCallRecord
from sextante.matching.domain.choice_resolution import LineChoice, resolve_line_choices
from sextante.matching.domain.item_choice import (
    CandidateItem,
    InvoiceContext,
    ItemChoiceFromModel,
    ItemChoiceRequest,
    LineToCode,
)
from sextante.matching.domain.line_decision import (
    FlagReason,
    LineDecision,
    LineNote,
    decide_line,
    non_service_line_decision,
    uncoded_line_decision,
)
from sextante.matching.domain.scoring import LexicalScore
from sextante.platform.audit import AuditEventRepository
from sextante.platform.clock import Clock, IdentifierGenerator
from sextante.platform.retry import RetryPolicy, Sleep, call_with_retries
from sextante.platform.text_normalization import normalize_for_comparison

logger = logging.getLogger(__name__)

# Writes another module makes in the same transaction as the line records, so that the
# entity verdict and the lines it produced are stored together or not at all.
SameTransactionWrite = Callable[[AsyncConnection], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class EncodingCollaborators:
    """Everything EncodeInvoice needs, injected (04-padroes-de-codigo.md §4)."""

    engine: AsyncEngine
    catalog: Catalog
    scorer: LexicalScorer
    classifier: ItemClassifier
    repository: MatchingRepositoryPort
    audit: AuditEventRepository
    clock: Clock
    identifiers: IdentifierGenerator
    fallback_item: CatalogItem
    generic_items: frozenset[ItemNumber]
    retry_policy: RetryPolicy
    sleep: Sleep


@dataclass(frozen=True, slots=True)
class _LineOutcome:
    """What one line ends up with, before it gets its identifiers and timestamp."""

    line: StoredLine
    choice: LineChoice | None
    decision: LineDecision
    scores: tuple[LexicalScore, ...]


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
    ) -> None:
        """Code the service lines with one model call; record VAT and discount lines as such.

        ``invoice_flags`` concern the whole invoice, such as a possible duplicate, and are
        added to every line, sending it to review (REQ-ING-011).

        Example:
            await encoder.execute(stored_invoice, TargetSheet.OUTLAYS, record_header)
        """
        services = [line for line in invoice.lines if line.line_type is LineType.SERVICE]
        others = [
            _non_service_outcome(line)
            for line in invoice.lines
            if line.line_type is not LineType.SERVICE
        ]
        call, coded = await self._code_services(invoice, services, target_sheet)
        outcomes = sorted(coded + others, key=lambda outcome: outcome.line.position)
        flagged = [_with_flags(outcome, invoice_flags) for outcome in outcomes]
        await self._persist(flagged, target_sheet, call, also_write)

    async def _code_services(
        self, invoice: StoredInvoice, services: list[StoredLine], target_sheet: TargetSheet
    ) -> tuple[ModelCallRecord | None, list[_LineOutcome]]:
        # No service line, no model call: there is nothing to choose (REQ-ING-006).
        if not services:
            return None, []
        deps = self._collaborators
        sheet_items = deps.catalog.items_of(target_sheet)
        scores = {
            line.line_id: deps.scorer.score(line.description, sheet_items) for line in services
        }
        call, choices = await self._ask_model(invoice, services, sheet_items, target_sheet)
        decide = self._decide
        outcomes = [
            decide(line, choices[line.position], scores[line.line_id], target_sheet)
            for line in services
        ]
        return call, outcomes

    async def _ask_model(
        self,
        invoice: StoredInvoice,
        services: list[StoredLine],
        sheet_items: tuple[CatalogItem, ...],
        target_sheet: TargetSheet,
    ) -> tuple[ModelCallRecord, dict[int, LineChoice]]:
        deps = self._collaborators
        # The model call is made outside any transaction: it takes seconds (D-3.3).
        request = item_choice_request(invoice, services, sheet_items)
        response = await call_with_retries(
            lambda: deps.classifier.choose(request),
            ItemClassifierUnavailableError,
            deps.retry_policy,
            deps.sleep,
        )
        positions = [line.position for line in services]
        choices = resolve_line_choices(
            positions, sheet_items, target_sheet, _validated(response.choices)
        )
        call = ModelCallRecord(
            deps.identifiers.new_id(), invoice.invoice_id, response, deps.clock.now()
        )
        return call, choices

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
        outcomes = [_LineOutcome(line, None, decision, ()) for line in invoice.lines]
        await self._persist(
            [_with_flags(o, invoice_flags) for o in outcomes], None, None, also_write
        )

    def _decide(
        self,
        line: StoredLine,
        choice: LineChoice,
        scores: tuple[LexicalScore, ...],
        target_sheet: TargetSheet,
    ) -> _LineOutcome:
        deps = self._collaborators
        decision = decide_line(choice, target_sheet, scores, deps.fallback_item, deps.generic_items)
        return _LineOutcome(line, choice, decision, scores)

    async def _persist(
        self,
        outcomes: list[_LineOutcome],
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
            await deps.repository.supersede_codings(connection, line_ids, deps.clock.now())
            if call is not None:
                await deps.repository.record_model_call(connection, call)
            for outcome in outcomes:
                await self._persist_line(connection, outcome, target_sheet, call)

    async def _persist_line(
        self,
        connection: AsyncConnection,
        outcome: _LineOutcome,
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
        self, outcome: _LineOutcome, target_sheet: TargetSheet | None, call: ModelCallRecord | None
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


def _validated(choices: Sequence[ItemChoiceFromModel]) -> list[ItemChoiceFromModel]:
    # Every answer goes through the schema again, whatever the adapter did: an answer
    # that fails it is dropped, and its line becomes an invalid response (SEC-14, REQ-MAP-007).
    valid: list[ItemChoiceFromModel] = []
    for choice in choices:
        try:
            valid.append(ItemChoiceFromModel.model_validate(choice.model_dump()))
        except ValidationError:
            logger.warning(
                "model_answer_rejected_by_schema", extra={"line_position": choice.line_position}
            )
    return valid


def _with_flags(outcome: _LineOutcome, flags: tuple[FlagReason, ...]) -> _LineOutcome:
    if not flags:
        return outcome
    decision = dataclasses.replace(outcome.decision, flags=outcome.decision.flags + flags)
    return dataclasses.replace(outcome, decision=decision)


def _non_service_outcome(line: StoredLine) -> _LineOutcome:
    note = LineNote.LINE_TYPE_TAX if line.line_type is LineType.TAX else LineNote.LINE_TYPE_DISCOUNT
    return _LineOutcome(line, None, non_service_line_decision(note), ())


def item_choice_request(
    invoice: StoredInvoice, services: list[StoredLine], sheet_items: tuple[CatalogItem, ...]
) -> ItemChoiceRequest:
    """The one request per invoice: its context, its service lines, the whole sheet (D-3.16).

    Example:
        item_choice_request(stored, services, catalog.items_of(TargetSheet.OUTLAYS))
    """
    return ItemChoiceRequest(
        context=InvoiceContext(supplier_name=invoice.supplier_name, currency=invoice.currency),
        lines=tuple(LineToCode(line.position, line.description) for line in services),
        candidates=tuple(
            CandidateItem(
                index,
                catalog_item.item_number.value,
                catalog_item.description_pt,
                catalog_item.description_en,
            )
            for index, catalog_item in enumerate(sheet_items)
        ),
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
