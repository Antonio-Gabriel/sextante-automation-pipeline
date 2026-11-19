"""Export rules as pure functions: formula neutralization and Invoice_ID (SEC-17, REQ-EXP-006)."""

import pytest

from sextante.export.domain.formula_neutralization import neutralize_formula
from sextante.export.domain.invoice_identifier import invoice_identifier
from sextante.platform.language import Language


@pytest.mark.requirement("REQ-EXP-003", "SEC-17")
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("=cmd|' /C calc'!A0", "'=cmd|' /C calc'!A0"),
        ("+351 sum", "'+351 sum"),
        ("-10000.00", "'-10000.00"),
        ("@SUM(A1)", "'@SUM(A1)"),
        ("\tleading tab", "'\tleading tab"),
        ("\rleading return", "'\rleading return"),
        ("Bilhete Avião", "Bilhete Avião"),
        ("a = b", "a = b"),
        ("", ""),
    ],
)
def test_a_leading_formula_trigger_is_prefixed_with_an_apostrophe(
    value: str, expected: str
) -> None:
    """Only a leading trigger matters: that is what a spreadsheet reads as a formula."""
    assert neutralize_formula(value) == expected


@pytest.mark.requirement("REQ-EXP-006", "D-3.10")
@pytest.mark.parametrize(
    ("supplier_nif", "supplier_name", "number", "expected"),
    [
        ("5419990001", "Companhia Aérea Sintética", "SYN-2026-001", "5419990001/SYN-2026-001"),
        ("NIF: 541 999 0001", "Companhia Sintética", "FT 2026/0001", "5419990001/FT 2026/0001"),
        (None, "Hotel Sintético, Lda.", "HTL-SYN-0001", "hotel sintetico lda/HTL-SYN-0001"),
        ("5419990001", "Companhia Sintética", None, "5419990001/3f2a9c1b0d4e"),
        (None, None, None, "3f2a9c1b0d4e"),
        ("5419990001", "Companhia Sintética", "   ", "5419990001/3f2a9c1b0d4e"),
    ],
    ids=[
        "NIF and number",
        "NIF with spaces",
        "no NIF",
        "no number",
        "nothing extracted",
        "blank number",
    ],
)
def test_invoice_id_combines_supplier_and_number(
    supplier_nif: str | None, supplier_name: str | None, number: str | None, expected: str
) -> None:
    """Supplier by NIF, else by normalized name; a short digest stands in for the number."""
    digest = "3f2a9c1b0d4e" + "0" * 52

    assert invoice_identifier(supplier_nif, supplier_name, number, digest) == expected


@pytest.mark.requirement("REQ-EXP-003", "SEC-17")
def test_neutralization_reaches_all_nine_columns() -> None:
    """Every column may carry supplier content, so none is exempt (SEC-17)."""
    from sextante.export.domain.export_rows import EXPORT_COLUMNS, ExportRow, export_cells

    row = ExportRow(*(f"=column {index}" for index in range(len(EXPORT_COLUMNS))))

    assert all(cell.startswith("'=") for cell in export_cells(row))


@pytest.mark.requirement("REQ-EXP-007", "REQ-PLT-006")
def test_every_rejection_reason_has_a_portuguese_export_message() -> None:
    """A new rejection reason without text would turn an export into a server error."""
    from sextante.export.application.build_job_export import rejection_message
    from sextante.ingestion.contracts import RejectionReason

    assert all(rejection_message(reason.value, Language.PT) for reason in RejectionReason)
    assert rejection_message("not-a-known-reason", Language.PT) == rejection_message(
        None, Language.PT
    )
