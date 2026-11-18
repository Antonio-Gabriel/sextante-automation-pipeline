"""Lexical scoring of a line against the whole target sheet (REQ-MAP-004, D-3.16)."""

import pytest

from sextante.catalog.contracts import CatalogItem, ItemNumber, TargetSheet
from sextante.matching.infrastructure.rapidfuzz_scorer import RapidfuzzLexicalScorer


def _catalog_item(number: str, description_pt: str, description_en: str) -> CatalogItem:
    return CatalogItem(
        ItemNumber(number),
        TargetSheet.OUTLAYS,
        description_pt,
        description_en,
        description_pt,
        description_en,
    )


@pytest.mark.requirement("REQ-MAP-004")
def test_english_line_scores_through_the_english_description() -> None:
    """The score is the better of the PT and EN comparisons."""
    sheet = (
        _catalog_item("O00004", "Bilhete Avião", "Air ticket"),
        _catalog_item("O00051", "Correio Express", "Express Courier"),
    )

    scores = RapidfuzzLexicalScorer().score("Air ticket on a test route", sheet)

    assert [(s.item_number, s.rank) for s in scores] == [("O00004", 1), ("O00051", 2)]
    assert scores[0].score == 100.0


@pytest.mark.requirement("REQ-MAP-004", "D-3.16")
def test_every_item_of_the_sheet_is_scored_even_when_unrelated() -> None:
    """Scores do not filter the list: every item gets one, ranked without gaps."""
    sheet = tuple(_catalog_item(f"O0000{n}", f"Item {n}", "") for n in range(1, 6))

    scores = RapidfuzzLexicalScorer().score("Sobrestadia de contentor", sheet)

    assert sorted(s.item_number for s in scores) == [f"O0000{n}" for n in range(1, 6)]
    assert [s.rank for s in scores] == [1, 2, 3, 4, 5]
