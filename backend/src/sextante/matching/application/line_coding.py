"""Decide the lines of one routed invoice, without storing anything (REQ-MAP-004 to 009, SEC-14).

One model call per invoice, with retries for transient failures; every answer validated
against the schema and the server's list; then the confidence rule. EncodeInvoice
stores what this decides, and the manual golden measurement reads it: both run the same
code, so they cannot drift apart.
"""

import dataclasses
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType

from pydantic import ValidationError

from sextante.catalog.contracts import Catalog, CatalogItem, ItemNumber, TargetSheet
from sextante.ingestion.contracts import LineType, StoredInvoice, StoredLine
from sextante.matching.application.ports import (
    ItemClassifier,
    ItemClassifierUnavailableError,
    LexicalScorer,
)
from sextante.matching.domain.choice_resolution import LineChoice, resolve_line_choices
from sextante.matching.domain.item_choice import (
    CandidateItem,
    InvoiceContext,
    ItemChoiceFromModel,
    ItemChoiceRequest,
    ItemChoiceResponse,
    LineToCode,
)
from sextante.matching.domain.line_decision import (
    FlagReason,
    LineDecision,
    LineNote,
    decide_line,
    non_service_line_decision,
)
from sextante.matching.domain.scoring import LexicalScore
from sextante.platform.retry import RetryPolicy, Sleep, call_with_retries

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CodingRules:
    """What deciding a line needs: the catalog, the scorer, the model and the rules' items."""

    catalog: Catalog
    scorer: LexicalScorer
    classifier: ItemClassifier
    fallback_item: CatalogItem
    generic_items: frozenset[ItemNumber]
    retry_policy: RetryPolicy
    sleep: Sleep


@dataclass(frozen=True, slots=True)
class LineOutcome:
    """What one line ends up with, before it gets its identifiers and timestamp."""

    line: StoredLine
    choice: LineChoice | None
    decision: LineDecision
    scores: tuple[LexicalScore, ...]


@dataclass(frozen=True, slots=True)
class CodedInvoice:
    """The model's response, when a call was made, and every line's outcome by position."""

    response: ItemChoiceResponse | None
    outcomes: tuple[LineOutcome, ...]


class LineCoder:
    """Code the service lines of an invoice; VAT and discount lines are recorded as such.

    Example:
        coded = await LineCoder(rules).code(stored_invoice, TargetSheet.OUTLAYS)
    """

    def __init__(self, rules: CodingRules) -> None:
        self._rules = rules

    async def code(
        self,
        invoice: StoredInvoice,
        target_sheet: TargetSheet,
        invoice_flags: tuple[FlagReason, ...] = (),
        line_flags: Mapping[str, tuple[FlagReason, ...]] = MappingProxyType({}),
    ) -> CodedInvoice:
        """Decide every line. ``invoice_flags`` go on every line, such as a duplicate;
        ``line_flags`` on the lines they name, such as a superseded review.

        Example:
            (await coder.code(stored, TargetSheet.OUTLAYSP)).outcomes[0].decision.confidence

        Raises:
            ItemClassifierUnavailableError: when the model stays unavailable after retries.
        """
        services = [line for line in invoice.lines if line.line_type is LineType.SERVICE]
        others = [_non_service_outcome(line) for line in invoice.lines if line not in services]
        response, coded = await self._code_services(invoice, services, target_sheet)
        outcomes = sorted(coded + others, key=lambda outcome: outcome.line.position)
        flagged = (
            with_flags(o, invoice_flags + line_flags.get(o.line.line_id, ())) for o in outcomes
        )
        return CodedInvoice(response, tuple(flagged))

    async def _code_services(
        self, invoice: StoredInvoice, services: list[StoredLine], target_sheet: TargetSheet
    ) -> tuple[ItemChoiceResponse | None, list[LineOutcome]]:
        # No service line, no model call: there is nothing to choose (REQ-ING-006).
        if not services:
            return None, []
        rules = self._rules
        sheet_items = rules.catalog.items_of(target_sheet)
        response = await call_with_retries(
            lambda: rules.classifier.choose(item_choice_request(invoice, services, sheet_items)),
            ItemClassifierUnavailableError,
            rules.retry_policy,
            rules.sleep,
        )
        positions = [line.position for line in services]
        choices = resolve_line_choices(
            positions, sheet_items, target_sheet, _validated(response.choices)
        )
        outcomes = [
            self._decide(line, choices[line.position], sheet_items, target_sheet)
            for line in services
        ]
        return response, outcomes

    def _decide(
        self,
        line: StoredLine,
        choice: LineChoice,
        sheet_items: tuple[CatalogItem, ...],
        target_sheet: TargetSheet,
    ) -> LineOutcome:
        rules = self._rules
        scores = rules.scorer.score(line.description, sheet_items)
        decision = decide_line(
            choice, target_sheet, scores, rules.fallback_item, rules.generic_items
        )
        return LineOutcome(line, choice, decision, scores)


def with_flags(outcome: LineOutcome, flags: tuple[FlagReason, ...]) -> LineOutcome:
    """The outcome with invoice-wide flags added, which send the line to review.

    Example:
        with_flags(outcome, (FlagReason.POSSIBLE_DUPLICATE,))
    """
    if not flags:
        return outcome
    decision = dataclasses.replace(outcome.decision, flags=outcome.decision.flags + flags)
    return dataclasses.replace(outcome, decision=decision)


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


def _non_service_outcome(line: StoredLine) -> LineOutcome:
    note = LineNote.LINE_TYPE_TAX if line.line_type is LineType.TAX else LineNote.LINE_TYPE_DISCOUNT
    return LineOutcome(line, None, non_service_line_decision(note), ())
