"""Catalog item values (D-3.9): presentation keeps the source, comparison is normalized."""

from typing import Final

import pytest

from sextante.catalog.domain.catalog_builder import (
    EXPECTED_HEADER,
    RawCatalogRow,
    RawCatalogSheet,
    build_catalog,
)
from sextante.catalog.domain.model import CatalogDigest, CatalogItem, TargetSheet

HEADER: Final = EXPECTED_HEADER
FALLBACK_ROW: Final = RawCatalogRow(
    2, ("O00999", "Despesas faturadas com o nome do cliente", "Client")
)


def _only_outlays_item(cells: tuple[str | None, ...]) -> CatalogItem:
    sheets = {
        "OUTLAYS": RawCatalogSheet(header=HEADER, rows=(RawCatalogRow(2, cells),)),
        "OUTLAYSP": RawCatalogSheet(header=HEADER, rows=(FALLBACK_ROW,)),
    }
    return build_catalog(sheets, CatalogDigest("0" * 64)).catalog.items_of(TargetSheet.OUTLAYS)[0]


@pytest.mark.requirement("REQ-MAP-003", "REQ-MAP-010", "D-3.9")
def test_presentation_values_keep_the_exact_code_and_trim_only_the_ends() -> None:
    """The exported description is the catalog text, trimmed at the ends only."""
    catalog_item = _only_outlays_item(("S00109", "  Despesas  de porto ", " Port  costs"))

    assert catalog_item.item_number.value == "S00109"
    assert catalog_item.description_pt == "Despesas  de porto"
    assert catalog_item.description_en == "Port  costs"


@pytest.mark.requirement("D-3.9", "D-3.16")
def test_comparison_values_drop_invisible_characters_and_collapse_spaces() -> None:
    """The zero-width space and doubled spaces of the real catalog do not reach scoring."""
    catalog_item = _only_outlays_item(("O00060", "Bilhete  Passagem", " Sea ​Ppassage Ticket"))

    assert catalog_item.comparison_pt == "Bilhete Passagem"
    assert catalog_item.comparison_en == "Sea Ppassage Ticket"


@pytest.mark.requirement("D-3.9")
def test_comparison_values_turn_non_breaking_spaces_into_plain_spaces() -> None:
    """NFKC folds the non-breaking spaces found in O00010 of the real catalog."""
    catalog_item = _only_outlays_item(("O00010", "Certificado\xa0de\xa0desratização", None))

    assert catalog_item.comparison_pt == "Certificado de desratização"
    assert catalog_item.comparison_en == ""


@pytest.mark.requirement("REQ-MAP-002")
def test_each_sheet_holds_only_its_own_items() -> None:
    """Sheets never mix: OUTLAYSP items are never served as OUTLAYS items."""
    sheets = {
        "OUTLAYS": RawCatalogSheet(header=HEADER, rows=(RawCatalogRow(2, ("O00004", "A", "A")),)),
        "OUTLAYSP": RawCatalogSheet(header=HEADER, rows=(FALLBACK_ROW,)),
    }
    catalog = build_catalog(sheets, CatalogDigest("0" * 64)).catalog

    assert [
        catalog_item.item_number.value for catalog_item in catalog.items_of(TargetSheet.OUTLAYS)
    ] == ["O00004"]
    assert [
        catalog_item.item_number.value for catalog_item in catalog.items_of(TargetSheet.OUTLAYSP)
    ] == ["O00999"]
