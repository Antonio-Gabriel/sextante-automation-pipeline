"""Build and validate the catalog from raw sheet rows (REQ-MAP-012). Pure: no I/O."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from sextante.catalog.domain.errors import CatalogValidationError
from sextante.catalog.domain.model import (
    FALLBACK_ITEM_NUMBER,
    Catalog,
    CatalogDigest,
    CatalogItem,
    ItemNumber,
    TargetSheet,
)
from sextante.platform.limits import MAX_SHEET_ITEMS
from sextante.platform.text_normalization import (
    has_invisible_characters,
    normalize_for_comparison,
)

# Columns B and C are read by position, so their headers are checked too: reading a
# moved column in silence is what L-05 forbids ("nunca inferir em silêncio", D-3.9).
EXPECTED_HEADER: Final = ("No.", "Description", "Description 2")
HEADER_COLUMNS: Final = "ABC"
DESCRIPTION_PT_POSITION: Final = 1
DESCRIPTION_EN_POSITION: Final = 2
CellValue = str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class RawCatalogRow:
    """One worksheet row as read from the file, with its 1-based row number."""

    row_number: int
    cells: tuple[CellValue, ...]

    def is_blank(self) -> bool:
        """Tell whether every cell of the row is empty.

        Example:
            RawCatalogRow(9, (None, None)).is_blank()  # True
        """
        return all(cell is None for cell in self.cells)

    def text_at(self, position: int) -> str:
        """Return the cell at ``position`` as text, or "" when the cell is empty or absent.

        Example:
            RawCatalogRow(2, ("O00004", "Bilhete Avião")).text_at(1)  # "Bilhete Avião"
        """
        value = self.cells[position] if position < len(self.cells) else None
        return "" if value is None else str(value)


@dataclass(frozen=True, slots=True)
class RawCatalogSheet:
    """One worksheet as read from the file: the header row and the data rows."""

    header: tuple[CellValue, ...]
    rows: tuple[RawCatalogRow, ...]


class CatalogWarningKind(StrEnum):
    """Catalog quirks worth a startup warning but not a refusal (D-3.9)."""

    INVISIBLE_CHARACTERS = "invisible_characters"
    MISSING_ENGLISH_DESCRIPTION = "missing_english_description"


@dataclass(frozen=True, slots=True)
class CatalogWarning:
    """A startup warning about one catalog item."""

    sheet: TargetSheet
    item_number: ItemNumber
    kind: CatalogWarningKind


@dataclass(frozen=True, slots=True)
class BuiltCatalog:
    """The validated catalog and the warnings found while building it."""

    catalog: Catalog
    warnings: tuple[CatalogWarning, ...]


def build_catalog(raw_sheets: Mapping[str, RawCatalogSheet], digest: CatalogDigest) -> BuiltCatalog:
    """Validate both sheets and build the in-memory catalog.

    ``raw_sheets`` is keyed by the worksheet title as found in the file, which may include
    sheets that are not catalog sheets; only OUTLAYS and OUTLAYSP are read.

    Example:
        built = build_catalog({"OUTLAYS": outlays, "OUTLAYSP": outlaysp}, digest)

    Raises:
        CatalogValidationError: naming the sheet and the violated condition.
    """
    outlays, outlays_warnings = _build_sheet(raw_sheets, TargetSheet.OUTLAYS)
    outlaysp, outlaysp_warnings = _build_sheet(raw_sheets, TargetSheet.OUTLAYSP)
    _require_fallback_item(outlaysp)
    catalog = Catalog(digest=digest, outlays=outlays, outlaysp=outlaysp)
    return BuiltCatalog(catalog=catalog, warnings=outlays_warnings + outlaysp_warnings)


def _build_sheet(
    raw_sheets: Mapping[str, RawCatalogSheet], sheet: TargetSheet
) -> tuple[tuple[CatalogItem, ...], tuple[CatalogWarning, ...]]:
    raw_sheet = raw_sheets.get(sheet.value)
    if raw_sheet is None:
        raise CatalogValidationError(
            f"Catalog sheet {sheet.value} is missing. Expected sheets OUTLAYS and OUTLAYSP."
        )
    _check_header(raw_sheet.header, sheet)
    rows = tuple(row for row in raw_sheet.rows if not row.is_blank())
    catalog_items = tuple(_build_catalog_item(row, sheet) for row in rows)
    _check_unique(catalog_items, sheet)
    _check_size(catalog_items, sheet)
    warnings = tuple(
        warning
        for row, catalog_item in zip(rows, catalog_items, strict=True)
        for warning in _warnings_for(row, catalog_item)
    )
    return catalog_items, warnings


def _check_header(header: tuple[CellValue, ...], sheet: TargetSheet) -> None:
    for position, expected in enumerate(EXPECTED_HEADER):
        found = header[position] if position < len(header) else None
        if found != expected:
            raise CatalogValidationError(
                f"Catalog sheet {sheet.value}: column {HEADER_COLUMNS[position]} header is "
                f"{found!r}, expected {expected!r}."
            )


def _build_catalog_item(row: RawCatalogRow, sheet: TargetSheet) -> CatalogItem:
    description_pt = row.text_at(DESCRIPTION_PT_POSITION)
    description_en = row.text_at(DESCRIPTION_EN_POSITION)
    return CatalogItem(
        item_number=_read_item_number(row, sheet),
        sheet=sheet,
        description_pt=description_pt.strip(),
        description_en=description_en.strip(),
        comparison_pt=normalize_for_comparison(description_pt),
        comparison_en=normalize_for_comparison(description_en),
    )


def _read_item_number(row: RawCatalogRow, sheet: TargetSheet) -> ItemNumber:
    raw_value = row.cells[0] if row.cells else None
    location = f"Catalog sheet {sheet.value}, row {row.row_number}"
    if raw_value is None or raw_value == "":
        raise CatalogValidationError(
            f"{location}: empty item number in column A. Expected the exact text of column "
            "No., for example 'O00004'."
        )
    if not isinstance(raw_value, str):
        raise CatalogValidationError(
            f"{location}: item number {raw_value!r} is not text. Expected the exact text of "
            "column No., for example 'O00004'."
        )
    try:
        return ItemNumber(raw_value)
    except ValueError as error:
        raise CatalogValidationError(f"{location}: {error}") from None


def _check_unique(catalog_items: tuple[CatalogItem, ...], sheet: TargetSheet) -> None:
    seen: set[ItemNumber] = set()
    for catalog_item in catalog_items:
        if catalog_item.item_number in seen:
            raise CatalogValidationError(
                f"Catalog sheet {sheet.value}: duplicate item number "
                f"{catalog_item.item_number.value!r}. Item numbers must be unique within a sheet."
            )
        seen.add(catalog_item.item_number)


def _check_size(catalog_items: tuple[CatalogItem, ...], sheet: TargetSheet) -> None:
    # The whole target sheet is sent to the model (D-3.16); this cap keeps the prompt
    # bounded (03-seguranca.md §9.1).
    if len(catalog_items) > MAX_SHEET_ITEMS:
        raise CatalogValidationError(
            f"Catalog sheet {sheet.value} has {len(catalog_items)} items, more than the limit "
            f"of {MAX_SHEET_ITEMS} items sent to the model (03-seguranca.md §9.1)."
        )


def _require_fallback_item(outlaysp: tuple[CatalogItem, ...]) -> None:
    # The OUTLAYSP fallback rule assigns O00999 (R3, REQ-MAP-008): without it, the rule
    # would have nothing valid to assign.
    if all(catalog_item.item_number != FALLBACK_ITEM_NUMBER for catalog_item in outlaysp):
        raise CatalogValidationError(
            f"Catalog sheet OUTLAYSP has no item {FALLBACK_ITEM_NUMBER}, "
            "which the fallback rule requires (R3, REQ-MAP-008)."
        )


def _warnings_for(row: RawCatalogRow, catalog_item: CatalogItem) -> tuple[CatalogWarning, ...]:
    # The invisible-character check reads the raw cells: trimming would hide a
    # non-breaking space at either end of a description.
    raw_descriptions = row.text_at(DESCRIPTION_PT_POSITION) + row.text_at(DESCRIPTION_EN_POSITION)
    kinds: list[CatalogWarningKind] = []
    if has_invisible_characters(raw_descriptions):
        kinds.append(CatalogWarningKind.INVISIBLE_CHARACTERS)
    if not catalog_item.comparison_en:
        kinds.append(CatalogWarningKind.MISSING_ENGLISH_DESCRIPTION)
    return tuple(
        CatalogWarning(catalog_item.sheet, catalog_item.item_number, kind) for kind in kinds
    )
