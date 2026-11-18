"""Turn the model's answers into catalog items, or refuse them (SEC-14 layers 3 and 4)."""

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from sextante.catalog.contracts import CatalogItem, TargetSheet
from sextante.matching.domain.item_choice import ItemChoiceFromModel


class ChoiceOutcome(StrEnum):
    """What came of one line's answer."""

    CHOSEN = "chosen"
    NO_ITEM_FITS = "no_item_fits"
    INVALID_RESPONSE = "invalid_response"


@dataclass(frozen=True, slots=True)
class LineChoice:
    """The resolved decision for one line. ``catalog_item`` is set only when CHOSEN."""

    outcome: ChoiceOutcome
    candidate_index: int | None
    catalog_item: CatalogItem | None


def resolve_line_choices(
    positions: Sequence[int],
    candidates: Sequence[CatalogItem],
    target_sheet: TargetSheet,
    answers: Sequence[ItemChoiceFromModel],
) -> dict[int, LineChoice]:
    """Resolve each line's answer against the list the server built.

    A line without exactly one answer, an index outside the list, or an item outside the
    target sheet is an invalid response, never an improvised code (REQ-MAP-005/007).

    Example:
        choices = resolve_line_choices([1], outlays_items, TargetSheet.OUTLAYS, answers)
    """
    answer_count = Counter(answer.line_position for answer in answers)
    by_position = {answer.line_position: answer for answer in answers}
    return {
        position: _resolve_one(
            by_position.get(position), answer_count[position], candidates, target_sheet
        )
        for position in positions
    }


def _resolve_one(
    answer: ItemChoiceFromModel | None,
    count: int,
    candidates: Sequence[CatalogItem],
    target_sheet: TargetSheet,
) -> LineChoice:
    if answer is None or count != 1:
        return LineChoice(ChoiceOutcome.INVALID_RESPONSE, None, None)
    index = answer.candidate_index
    if index is None:
        return LineChoice(ChoiceOutcome.NO_ITEM_FITS, None, None)
    if index >= len(candidates) or candidates[index].sheet is not target_sheet:
        return LineChoice(ChoiceOutcome.INVALID_RESPONSE, index, None)
    return LineChoice(ChoiceOutcome.CHOSEN, index, candidates[index])
