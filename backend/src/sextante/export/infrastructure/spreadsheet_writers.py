"""Write export rows as CSV (UTF-8 with BOM) or XLSX (REQ-EXP-002, REQ-EXP-005, SEC-17)."""

import csv
import io
from collections.abc import Sequence
from typing import Final

from openpyxl import Workbook

from sextante.export.application.ports import ExportFile, ExportFormat
from sextante.export.domain.export_rows import EXPORT_COLUMNS, ExportRow, export_cells

# Excel in a Portuguese locale opens UTF-8 without a BOM with broken accents (REQ-EXP-005).
UTF8_WITH_BOM: Final = "utf-8-sig"
XLSX_SHEET_TITLE: Final = "Sextante"
CSV_MEDIA_TYPE: Final = "text/csv; charset=utf-8"
XLSX_MEDIA_TYPE: Final = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class SpreadsheetExportWriter:
    """Implements SpreadsheetWriter: CSV with the configured separator, or XLSX.

    Example:
        SpreadsheetExportWriter(",").write(rows, ExportFormat.CSV).extension  # "csv"
    """

    def __init__(self, csv_separator: str) -> None:
        self._csv_separator = csv_separator

    def write(self, rows: Sequence[ExportRow], export_format: ExportFormat) -> ExportFile:
        """Return the file for these rows in the requested format."""
        if export_format is ExportFormat.CSV:
            return ExportFile(write_csv(rows, self._csv_separator), CSV_MEDIA_TYPE, "csv")
        return ExportFile(write_xlsx(rows), XLSX_MEDIA_TYPE, "xlsx")


def write_csv(rows: Sequence[ExportRow], separator: str) -> bytes:
    """Write the header and rows with csv.writer, never by string concatenation (SEC-17).

    Example:
        write_csv(rows, ",")[:3]  # b"\\xef\\xbb\\xbf"
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=separator, lineterminator="\r\n")
    writer.writerow(EXPORT_COLUMNS)
    writer.writerows(export_cells(row) for row in rows)
    return buffer.getvalue().encode(UTF8_WITH_BOM)


def write_xlsx(rows: Sequence[ExportRow]) -> bytes:
    """Write the header and rows with every cell typed as text, besides the prefix (SEC-17).

    Example:
        write_xlsx(rows)[:2]  # b"PK"
    """
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = XLSX_SHEET_TITLE
    for row_index, cells in enumerate([list(EXPORT_COLUMNS), *map(export_cells, rows)], start=1):
        for column_index, value in enumerate(cells, start=1):
            cell = sheet.cell(row=row_index, column=column_index)
            cell.value = value
            cell.data_type = "s"
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
