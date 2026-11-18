"""The nine export columns and how a row becomes cells (R6, REQ-EXP-001, SEC-17)."""

from dataclasses import astuple, dataclass
from typing import Final

from sextante.export.domain.formula_neutralization import neutralize_formula

EXPORT_COLUMNS: Final = (
    "Invoice_ID",
    "Billed_Entity_Detected",
    "Exact_Entity_Match",
    "Target_Sheet",
    "Line_Description",
    "Assigned_Item_No",
    "Matched_Catalog_Description",
    "Confidence",
    "Notes_or_Flags",
)
NOTES_SEPARATOR: Final = "; "


@dataclass(frozen=True, slots=True)
class ExportRow:
    """One exported row, field for field the nine columns, in their order."""

    invoice_id: str
    billed_entity_detected: str
    exact_entity_match: str
    target_sheet: str
    line_description: str
    assigned_item_no: str
    matched_catalog_description: str
    confidence: str
    notes_or_flags: str


def export_cells(row: ExportRow) -> list[str]:
    """The row as cells, every one neutralized: the single point of SEC-17.

    Every column may carry supplier content, so no column is exempt; a list of columns
    to treat would age badly (SEC-17).

    Example:
        export_cells(row)[4]  # "'=cmd|..." for a description starting with "="
    """
    return [neutralize_formula(value) for value in astuple(row)]
