"""Read the catalog workbook with openpyxl in read_only and data_only mode (D-3.9, SEC-09.5)."""

import hashlib
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

from openpyxl import load_workbook

from sextante.catalog.domain.catalog_builder import CellValue, RawCatalogRow, RawCatalogSheet
from sextante.catalog.domain.errors import CatalogFileError
from sextante.catalog.domain.model import CatalogDigest


class _Worksheet(Protocol):
    """The part of an openpyxl read-only worksheet this reader uses."""

    title: str

    def iter_rows(self, *, values_only: bool) -> Iterator[tuple[object, ...]]: ...


class XlsxCatalogWorkbookReader:
    """Implements the CatalogWorkbookReader port with openpyxl.

    Example:
        sheets = XlsxCatalogWorkbookReader().read_sheets(Path("catalog.xlsx"))
    """

    def digest(self, path: Path) -> CatalogDigest:
        """Return the SHA-256 of the catalog file content."""
        return CatalogDigest(hashlib.sha256(path.read_bytes()).hexdigest())

    def read_sheets(self, path: Path) -> dict[str, RawCatalogSheet]:
        """Read every worksheet as raw rows, without interpreting them.

        data_only reads computed values and never evaluates formulas; read_only streams
        rows instead of loading the whole workbook (03-seguranca.md SEC-09.5).

        Raises:
            CatalogFileError: when the file is not an xlsx workbook.
        """
        if not zipfile.is_zipfile(path):
            raise CatalogFileError(f"Catalog file {path.name!r} is not a valid xlsx workbook.")
        workbook = load_workbook(path, read_only=True, data_only=True)
        try:
            return {sheet.title: _read_sheet(sheet) for sheet in workbook.worksheets}
        finally:
            workbook.close()


def _read_sheet(sheet: _Worksheet) -> RawCatalogSheet:
    rows = [tuple(_cell(value) for value in row) for row in sheet.iter_rows(values_only=True)]
    header = rows[0] if rows else ()
    data_rows = tuple(
        RawCatalogRow(row_number=index, cells=cells)
        for index, cells in enumerate(rows[1:], start=2)
    )
    return RawCatalogSheet(header=header, rows=data_rows)


def _cell(value: object) -> CellValue:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    return str(value)
