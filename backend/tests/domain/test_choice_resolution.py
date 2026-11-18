"""SEC-14 layers 3 and 4, as pure rules: answers become catalog items or are refused."""

import pytest

from sextante.catalog.contracts import CatalogItem, ItemNumber, TargetSheet
from sextante.matching.domain.choice_resolution import ChoiceOutcome, resolve_line_choices
from sextante.matching.domain.item_choice import ItemChoiceFromModel


def _catalog_item(number: str, sheet: TargetSheet) -> CatalogItem:
    return CatalogItem(ItemNumber(number), sheet, number, number, number, number)


OUTLAYS_ITEMS = (
    _catalog_item("O00004", TargetSheet.OUTLAYS),
    _catalog_item("O00051", TargetSheet.OUTLAYS),
)


def _answer(position: int, index: int | None) -> ItemChoiceFromModel:
    return ItemChoiceFromModel(line_position=position, candidate_index=index)


@pytest.mark.requirement("SEC-14", "REQ-MAP-005")
def test_index_inside_the_list_resolves_to_that_catalog_item() -> None:
    """The index is the only thing the model gives; the code comes from the server's list."""
    choices = resolve_line_choices([1], OUTLAYS_ITEMS, TargetSheet.OUTLAYS, [_answer(1, 1)])

    assert choices[1].outcome is ChoiceOutcome.CHOSEN
    assert choices[1].catalog_item is OUTLAYS_ITEMS[1]


@pytest.mark.requirement("SEC-14")
def test_index_beyond_the_list_is_an_invalid_response() -> None:
    """Layer 3: the index is checked against the real length of the list."""
    choices = resolve_line_choices([1], OUTLAYS_ITEMS, TargetSheet.OUTLAYS, [_answer(1, 2)])

    assert choices[1].outcome is ChoiceOutcome.INVALID_RESPONSE
    assert choices[1].catalog_item is None


@pytest.mark.requirement("SEC-14", "REQ-MAP-002")
def test_item_from_another_sheet_is_an_invalid_response() -> None:
    """Layer 4: the item must belong to the sheet the server routed the line to."""
    mixed = (_catalog_item("O00999", TargetSheet.OUTLAYSP),)

    choices = resolve_line_choices([1], mixed, TargetSheet.OUTLAYS, [_answer(1, 0)])

    assert choices[1].outcome is ChoiceOutcome.INVALID_RESPONSE


@pytest.mark.requirement("SEC-14", "REQ-MAP-007")
@pytest.mark.parametrize("answers", [[], [_answer(1, 0), _answer(1, 1)]], ids=["none", "twice"])
def test_a_line_without_exactly_one_answer_is_an_invalid_response(
    answers: list[ItemChoiceFromModel],
) -> None:
    """A missing or repeated answer is a line failure, never a guess."""
    choices = resolve_line_choices([1], OUTLAYS_ITEMS, TargetSheet.OUTLAYS, answers)

    assert choices[1].outcome is ChoiceOutcome.INVALID_RESPONSE


@pytest.mark.requirement("REQ-MAP-005")
def test_none_means_no_item_fits_and_assigns_nothing() -> None:
    """The model's "none" is recorded as such; what it means per sheet is ticket 04."""
    choices = resolve_line_choices([1], OUTLAYS_ITEMS, TargetSheet.OUTLAYS, [_answer(1, None)])

    assert choices[1].outcome is ChoiceOutcome.NO_ITEM_FITS
    assert choices[1].catalog_item is None


@pytest.mark.requirement("SEC-14", "SEC-09")
@pytest.mark.parametrize(
    "bad", [{"candidate_index": "O00999"}, {"candidate_index": -1}, {"code": "O00999"}]
)
def test_model_answer_that_is_not_an_index_is_refused_by_schema(bad: dict[str, object]) -> None:
    """A free-text code, a negative index or an extra field never passes the schema."""
    with pytest.raises(ValueError):
        ItemChoiceFromModel.model_validate({"line_position": 1, "candidate_index": 0, **bad})
