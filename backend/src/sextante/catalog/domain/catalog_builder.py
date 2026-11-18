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

EXPECTED_HEADER: Final = ("No.", "Description", "Description 2")
CellValue = str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class RawCatalogRow:
    """One worksheet row as read from the file, with its 1-based row number."""

    row_number: int
    cells: tuple[CellValue, ...]


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
    items = tuple(
        _build_item(row, sheet) for row in raw_sheet.rows if any(c is not None for c in row.cells)
    )
    _check_unique(items, sheet)
    _check_size(items, sheet)
    return items, tuple(warning for item in items for warning in _warnings_for(item))


def _check_header(header: tuple[CellValue, ...], sheet: TargetSheet) -> None:
    for column, expected in zip("ABC", EXPECTED_HEADER, strict=True):
        position = "ABC".index(column)
        found = header[position] if position < len(header) else None
        if found != expected:
            raise CatalogValidationError(
                f"Catalog sheet {sheet.value}: column {column} header is {found!r}, "
                f"expected {expected!r}."
            )


def _build_item(row: RawCatalogRow, sheet: TargetSheet) -> CatalogItem:
    item_number = _read_item_number(row, sheet)
    description_pt = _cell_text(row, 1)
    description_en = _cell_text(row, 2)
    return CatalogItem(
        item_number=item_number,
        sheet=sheet,
        description_pt=description_pt.strip(),
        description_en=description_en.strip(),
        comparison_pt=normalize_for_comparison(description_pt),
        comparison_en=normalize_for_comparison(description_en),
    )


def _read_item_number(row: RawCatalogRow, sheet: TargetSheet) -> ItemNumber:
    raw_value = row.cells[0] if row.cells else None
    if raw_value is None or raw_value == "":
        raise CatalogValidationError(
            f"Catalog sheet {sheet.value}, row {row.row_number}: empty item number in column A."
        )
    if not isinstance(raw_value, str):
        raise CatalogValidationError(
            f"Catalog sheet {sheet.value}, row {row.row_number}: item number {raw_value!r} "
            "is not text. Expected the exact text of column No., for example 'O00004'."
        )
    try:
        return ItemNumber(raw_value)
    except ValueError as error:
        raise CatalogValidationError(
            f"Catalog sheet {sheet.value}, row {row.row_number}: {error}"
        ) from None


def _cell_text(row: RawCatalogRow, position: int) -> str:
    value = row.cells[position] if position < len(row.cells) else None
    return "" if value is None else str(value)


def _check_unique(items: tuple[CatalogItem, ...], sheet: TargetSheet) -> None:
    seen: set[ItemNumber] = set()
    for item in items:
        if item.item_number in seen:
            raise CatalogValidationError(
                f"Catalog sheet {sheet.value}: duplicate item number {item.item_number.value!r}. "
                "Item numbers must be unique within a sheet."
            )
        seen.add(item.item_number)


def _check_size(items: tuple[CatalogItem, ...], sheet: TargetSheet) -> None:
    # The whole target sheet is sent to the model (D-3.16); this cap keeps the prompt
    # bounded (03-seguranca.md §9.1).
    if len(items) > MAX_SHEET_ITEMS:
        raise CatalogValidationError(
            f"Catalog sheet {sheet.value} has {len(items)} items, more than the limit of "
            f"{MAX_SHEET_ITEMS} items sent to the model (03-seguranca.md §9.1)."
        )


def _require_fallback_item(outlaysp: tuple[CatalogItem, ...]) -> None:
    # The OUTLAYSP fallback rule assigns O00999 (R3, REQ-MAP-008): without it, the rule
    # would have nothing valid to assign.
    if all(item.item_number.value != FALLBACK_ITEM_NUMBER for item in outlaysp):
        raise CatalogValidationError(
            f"Catalog sheet OUTLAYSP has no item {FALLBACK_ITEM_NUMBER}, "
            "which the fallback rule requires (R3, REQ-MAP-008)."
        )


def _warnings_for(item: CatalogItem) -> tuple[CatalogWarning, ...]:
    kinds: list[CatalogWarningKind] = []
    if has_invisible_characters(item.description_pt + item.description_en):
        kinds.append(CatalogWarningKind.INVISIBLE_CHARACTERS)
    if not item.comparison_en:
        kinds.append(CatalogWarningKind.MISSING_ENGLISH_DESCRIPTION)
    return tuple(CatalogWarning(item.sheet, item.item_number, kind) for kind in kinds)
