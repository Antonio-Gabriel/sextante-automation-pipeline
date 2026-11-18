"""What each line ends up with: item, confidence, flags and review state (D-3.8, D-3.16).

Confidence is computed, never asked of the model (REQ-CNF-001). The thresholds live
here, in one place, and are provisional until the golden set calibrates them
(L-02, REQ-CNF-005).
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Literal

from sextante.catalog.contracts import CatalogItem, ItemNumber, TargetSheet
from sextante.matching.domain.choice_resolution import ChoiceOutcome, LineChoice
from sextante.matching.domain.scoring import LexicalScore

# HIGH needs a score strictly above ITEM_SCORE_HIGH and a lead strictly above
# ITEM_MARGIN_MIN over the second item ("acima", D-3.8).
ITEM_SCORE_HIGH: Final = 85
ITEM_MARGIN_MIN: Final = 10
# A sheet with a single item has no runner-up: nothing to fall short of, nothing to
# conflict with.
NO_RUNNER_UP_GAP: Final = math.inf


class Confidence(StrEnum):
    """Confidence of one line (REQ-CNF-002)."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class FlagReason(StrEnum):
    """Closed set of reasons that send a line to review (REQ-CNF-004)."""

    ENTITY_LABEL_NOT_FOUND = "entity_label_not_found"
    MULTIPLE_BILLED_ENTITIES = "multiple_billed_entities"
    ENTITY_SIMILAR_NOT_EQUAL = "entity_similar_not_equal"
    ENTITY_NIF_MISMATCH = "entity_nif_mismatch"
    NO_MATCH_IN_OUTLAYS = "no_match_in_outlays"
    FALLBACK_APPLIED = "fallback_applied"
    GENERIC_CATALOG_ITEM = "generic_catalog_item"
    CONFLICTING_CANDIDATES = "conflicting_candidates"
    MODEL_RESPONSE_INVALID = "model_response_invalid"
    POSSIBLE_DUPLICATE = "possible_duplicate"
    # A reviewer had decided this line; the new coding needs a new look (D-3.23).
    REVIEW_SUPERSEDED = "review_superseded"


ReviewStatus = Literal["pending", "accepted"]


@dataclass(frozen=True, slots=True)
class LineDecision:
    """The outcome for one line, with the rule that produced its confidence."""

    catalog_item: CatalogItem | None
    confidence: Confidence
    flags: tuple[FlagReason, ...]
    rule: str
    note: "LineNote | None" = None

    @property
    def review_status(self) -> ReviewStatus:
        """A flagged line starts pending, any other starts accepted (REQ-REV-005).

        Example:
            decide_line(...).review_status  # "pending"
        """
        return "pending" if self.flags else "accepted"


def decide_line(
    choice: LineChoice,
    target_sheet: TargetSheet,
    scores: Sequence[LexicalScore],
    fallback_item: CatalogItem,
    generic_items: frozenset[ItemNumber],
) -> LineDecision:
    """Turn the resolved model answer into the line's item, confidence and flags.

    Example:
        decide_line(choice, TargetSheet.OUTLAYSP, scores, o00999, frozenset({o00052}))
    """
    if choice.outcome is ChoiceOutcome.INVALID_RESPONSE:
        return _low(None, FlagReason.MODEL_RESPONSE_INVALID, "invalid_response")
    if choice.catalog_item is None:
        return _no_item_fits(target_sheet, fallback_item)
    if choice.catalog_item.item_number in generic_items:
        return _low(choice.catalog_item, FlagReason.GENERIC_CATALOG_ITEM, "generic_item")
    return _chosen(choice.catalog_item, scores)


class LineNote(StrEnum):
    """Information about a line that is not a reason for review (D-3.17)."""

    LINE_TYPE_TAX = "line_type_tax"
    LINE_TYPE_DISCOUNT = "line_type_discount"


def non_service_line_decision(note: LineNote) -> LineDecision:
    """A VAT or discount line: no code, HIGH, accepted, not flagged (D-3.17, REQ-ING-006).

    The classification is certain and there is no code to get wrong; flagging these
    lines would fill the review queue with easy cases.

    Example:
        non_service_line_decision(LineNote.LINE_TYPE_TAX).confidence  # Confidence.HIGH
    """
    return LineDecision(None, Confidence.HIGH, (), "non_service_line", note)


def uncoded_line_decision(reason: FlagReason) -> LineDecision:
    """The decision for a line of an ambiguous invoice: no item, LOW, flagged (D-3.15).

    Example:
        uncoded_line_decision(FlagReason.ENTITY_NIF_MISMATCH).confidence  # Confidence.LOW
    """
    return _low(None, reason, "entity_ambiguous")


def _no_item_fits(target_sheet: TargetSheet, fallback_item: CatalogItem) -> LineDecision:
    # The O00999 fallback is limited to OUTLAYSP and decided here, in code (R3, SEC-14).
    # OUTLAYS has none: the gap goes back to a reviewer (L-08, REQ-MAP-009).
    if target_sheet is TargetSheet.OUTLAYSP:
        return _low(fallback_item, FlagReason.FALLBACK_APPLIED, "fallback_outlaysp")
    return _low(None, FlagReason.NO_MATCH_IN_OUTLAYS, "no_match_outlays")


def _chosen(catalog_item: CatalogItem, scores: Sequence[LexicalScore]) -> LineDecision:
    chosen_rank = _rank_of(catalog_item, scores)
    gap = scores[0].score - scores[1].score if len(scores) > 1 else NO_RUNNER_UP_GAP
    top_is_high = bool(scores) and scores[0].score > ITEM_SCORE_HIGH
    if chosen_rank == 1 and top_is_high and gap > ITEM_MARGIN_MIN:
        return LineDecision(catalog_item, Confidence.HIGH, (), "high_agreement")
    # Conflicting only when the choice is one of two close leaders: a clear third
    # choice is the model disagreeing, not a toss-up (D-3.8).
    conflicting = chosen_rank in (1, 2) and gap <= ITEM_MARGIN_MIN
    flags = (FlagReason.CONFLICTING_CANDIDATES,) if conflicting else ()
    return LineDecision(catalog_item, Confidence.MEDIUM, flags, "medium_chosen")


def _rank_of(catalog_item: CatalogItem, scores: Sequence[LexicalScore]) -> int | None:
    wanted = catalog_item.item_number.value
    return next((score.rank for score in scores if score.item_number == wanted), None)


def _low(catalog_item: CatalogItem | None, flag: FlagReason, rule: str) -> LineDecision:
    return LineDecision(catalog_item, Confidence.LOW, (flag,), rule)
