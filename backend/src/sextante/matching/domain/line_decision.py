"""What each line ends up with: item, confidence, flags and review state (D-3.8, D-3.16).

Confidence is computed, never asked of the model (REQ-CNF-001). The thresholds live
here, in one place, and are provisional until the golden set calibrates them
(L-02, REQ-CNF-005).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Literal

from sextante.catalog.contracts import CatalogItem, ItemNumber, TargetSheet
from sextante.matching.domain.choice_resolution import ChoiceOutcome, LineChoice
from sextante.matching.domain.scoring import LexicalScore

ITEM_SCORE_HIGH: Final = 85
ITEM_MARGIN_MIN: Final = 10


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


ReviewStatus = Literal["pending", "accepted"]


@dataclass(frozen=True, slots=True)
class LineDecision:
    """The outcome for one line, with the rule that produced its confidence."""

    catalog_item: CatalogItem | None
    confidence: Confidence
    flags: tuple[FlagReason, ...]
    rule: str

    @property
    def review_status(self) -> ReviewStatus:
        """A flagged line starts pending, any other starts accepted (REQ-REV-005)."""
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


def _no_item_fits(target_sheet: TargetSheet, fallback_item: CatalogItem) -> LineDecision:
    # The O00999 fallback is limited to OUTLAYSP and decided here, in code (R3, SEC-14).
    # OUTLAYS has none: the gap goes back to a reviewer (L-08, REQ-MAP-009).
    if target_sheet is TargetSheet.OUTLAYSP:
        return _low(fallback_item, FlagReason.FALLBACK_APPLIED, "fallback_outlaysp")
    return _low(None, FlagReason.NO_MATCH_IN_OUTLAYS, "no_match_outlays")


def _chosen(catalog_item: CatalogItem, scores: Sequence[LexicalScore]) -> LineDecision:
    chosen_rank = _rank_of(catalog_item, scores)
    gap = scores[0].score - scores[1].score if len(scores) > 1 else float(ITEM_SCORE_HIGH)
    top_is_high = bool(scores) and scores[0].score >= ITEM_SCORE_HIGH
    if chosen_rank == 1 and top_is_high and gap >= ITEM_MARGIN_MIN:
        return LineDecision(catalog_item, Confidence.HIGH, (), "high_agreement")
    # Conflicting only when the choice is one of two close leaders: a clear third
    # choice is the model disagreeing, not a toss-up (D-3.8).
    conflicting = chosen_rank in (1, 2) and len(scores) > 1 and gap < ITEM_MARGIN_MIN
    flags = (FlagReason.CONFLICTING_CANDIDATES,) if conflicting else ()
    return LineDecision(catalog_item, Confidence.MEDIUM, flags, "medium_chosen")


def _rank_of(catalog_item: CatalogItem, scores: Sequence[LexicalScore]) -> int | None:
    wanted = catalog_item.item_number.value
    return next((score.rank for score in scores if score.item_number == wanted), None)


def _low(catalog_item: CatalogItem | None, flag: FlagReason, rule: str) -> LineDecision:
    return LineDecision(catalog_item, Confidence.LOW, (flag,), rule)
