"""Export rules as pure functions: formula neutralization and Invoice_ID (SEC-17, REQ-EXP-006)."""

import pytest

from sextante.export.domain.formula_neutralization import neutralize_formula
from sextante.export.domain.invoice_identifier import invoice_identifier


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
        ("NIF: 541 999 0001", "companhia aérea", "FT 2026/0001", "5419990001/FT 2026/0001"),
        (None, "Hotel Sintético, Lda.", "HTL-SYN-0001", "hotel sintetico lda/HTL-SYN-0001"),
        ("5419990001", "companhia aérea", None, "5419990001/3f2a9c1b0d4e"),
        (None, None, None, "3f2a9c1b0d4e"),
    ],
    ids=["NIF and number", "NIF with spaces", "no NIF", "no number", "nothing extracted"],
)
def test_invoice_id_combines_supplier_and_number(
    supplier_nif: str | None, supplier_name: str | None, number: str | None, expected: str
) -> None:
    """Supplier by NIF, else by normalized name; a short digest stands in for the number."""
    digest = "3f2a9c1b0d4e" + "0" * 52

    assert invoice_identifier(supplier_nif, supplier_name, number, digest) == expected
