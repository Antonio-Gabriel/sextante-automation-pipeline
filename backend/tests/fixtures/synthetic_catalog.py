"""Builder for SYNTHETIC catalog workbooks used in tests.

Not the real AMT catalog. It mirrors the real column structure (No., Description,
Description 2, ...) and the quirks found in the real file (D-3.9): O00999, a generic
item, a PT/EN pair that disagrees, an item without an English description, and a
description with an invisible character.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from openpyxl import Workbook

HEADER: tuple[str, ...] = (
    "No.",
    "Description",
    "Description 2",
    "Type",
    "Base Unit of Measure",
    "VAT Prod. Posting Group",
    "Gen. Prod. Posting Group",
)

CatalogRow = tuple[str | None, str | None, str | None]

DEFAULT_OUTLAYS: tuple[CatalogRow, ...] = (
    ("O00004", "Bilhete Avião", "Air ticket"),
    ("O00015", "Despesas ", "Storage fees"),
    ("O00051", "Correio Express", "Express Courier"),
    ("O00052", "Outras Despesas", "Other Expenses"),
    ("O00060", "Bilhete Passagem Maritima", " Sea ​Ppassage Ticket"),
    ("O00061", "Compra de bens", ""),
    ("S00109", "Transporte rodoviario", "Road freight"),
)

DEFAULT_OUTLAYSP: tuple[CatalogRow, ...] = (
    ("O00002", "Alfândegas", "Customs"),
    ("O00010", "Certificado\xa0de\xa0desratização", "Certificate of desratization"),
    ("O00031", "Sobrestadia Contentor", "Container demurrage"),
    ("O00999", "Despesas faturadas com o nome do cliente", "Invoice under the client's name"),
)


@dataclass
class SyntheticCatalog:
    """Declarative description of a synthetic catalog workbook.

    Example:
        path = SyntheticCatalog(outlaysp=()).write(tmp_path / "catalog.xlsx")
    """

    outlays: Sequence[CatalogRow] = DEFAULT_OUTLAYS
    outlaysp: Sequence[CatalogRow] = DEFAULT_OUTLAYSP
    sheet_names: tuple[str, ...] = ("OUTLAYS", "OUTLAYSP")
    header: tuple[str, ...] = HEADER
    extra_sheets: dict[str, Sequence[CatalogRow]] = field(default_factory=dict)

    def write(self, path: Path) -> Path:
        """Write the workbook to ``path`` and return it."""
        workbook = Workbook()
        workbook.remove(workbook.active)
        rows_by_sheet = {"OUTLAYS": self.outlays, "OUTLAYSP": self.outlaysp}
        for sheet_name in self.sheet_names:
            self._write_sheet(workbook, sheet_name, rows_by_sheet.get(sheet_name, ()))
        for sheet_name, rows in self.extra_sheets.items():
            self._write_sheet(workbook, sheet_name, rows)
        workbook.save(path)
        return path

    def _write_sheet(self, workbook: Workbook, name: str, rows: Sequence[CatalogRow]) -> None:
        sheet = workbook.create_sheet(name)
        sheet.append(list(self.header))
        for item_number, description, description_en in rows:
            sheet.append([item_number, description, description_en, "Service", "UNIT", "EXO", name])
