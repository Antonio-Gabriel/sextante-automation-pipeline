"""Ticket 06: export to CSV and XLSX (REQ-EXP-001 to REQ-EXP-007, SEC-17)."""

import csv
import io
from typing import Final

import pytest
from openpyxl import load_workbook

from tests.api.encoding_harness import export_bytes, running_application
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fixtures.synthetic_invoices import (
    SyntheticInvoice,
    air_ticket_to_amt,
    billed_to,
    scanned_pdf_without_text,
    service_with_vat_and_discount_lines,
    with_description,
)

COLUMNS: Final = [
    "Invoice_ID",
    "Billed_Entity_Detected",
    "Exact_Entity_Match",
    "Target_Sheet",
    "Line_Description",
    "Assigned_Item_No",
    "Matched_Catalog_Description",
    "Confidence",
    "Notes_or_Flags",
]
FORMULA: Final = "=cmd|' /C calc'!A0"


def _export(
    environment: dict[str, str],
    invoices: list[SyntheticInvoice],
    classifier: FakeItemClassifier,
    export_format: str = "csv",
) -> bytes:
    with running_application(environment, invoices, classifier) as app:
        files = [("files", (i.file_name, i.content, "application/pdf")) for i in invoices]
        job_id = app.client.post("/api/invoices", files=files).json()["job_id"]
        app.wait_for_job(job_id)
        return export_bytes(app, job_id, export_format)


def _csv_rows(content: bytes, separator: str = ",") -> list[list[str]]:
    assert content.startswith(b"\xef\xbb\xbf"), "CSV must start with a UTF-8 BOM"
    return list(csv.reader(io.StringIO(content.decode("utf-8-sig")), delimiter=separator))


def _xlsx_rows(content: bytes) -> list[list[object]]:
    # An empty text cell is not stored in XLSX, and openpyxl reads it back as None.
    sheet = load_workbook(io.BytesIO(content), read_only=True).worksheets[0]
    return [["" if v is None else v for v in row] for row in sheet.iter_rows(values_only=True)]


@pytest.mark.requirement("REQ-EXP-001", "REQ-EXP-002", "REQ-EXP-005", "R6")
@pytest.mark.parametrize("export_format", ["csv", "xlsx"])
def test_export_has_exactly_the_nine_columns_in_order(
    valid_environment: dict[str, str], export_format: str
) -> None:
    """Same header, same row, in CSV (UTF-8 with BOM) and in XLSX."""
    content = _export(
        valid_environment,
        [air_ticket_to_amt()],
        FakeItemClassifier({1: "O00004"}),
        export_format,
    )

    rows = _csv_rows(content) if export_format == "csv" else _xlsx_rows(content)
    assert rows[0] == COLUMNS
    assert rows[1] == [
        "5419990001/SYN-2026-001",
        "Advanced Maritime Transports - Transitarios Limitada",
        "YES",
        "OUTLAYS",
        "Passagem aérea Sintética - Rota Teste (Rotação equipa - Ref #SYN-0000001)",
        "O00004",
        "Bilhete Avião",
        "MEDIUM",
        "",
    ]


@pytest.mark.requirement("REQ-EXP-003", "SEC-17")
@pytest.mark.parametrize("export_format", ["csv", "xlsx"])
def test_every_text_cell_starting_with_a_formula_trigger_is_neutralized(
    valid_environment: dict[str, str], export_format: str
) -> None:
    """The description and the billed entity both come from the supplier."""
    invoice = billed_to("FORMULA", "@Evil Trading Lda")
    invoice = with_description(invoice, FORMULA, "FORMULA")

    content = _export(
        valid_environment, [invoice], FakeItemClassifier({1: "O00031"}), export_format
    )

    row = (_csv_rows(content) if export_format == "csv" else _xlsx_rows(content))[1]
    assert row[1] == "'@Evil Trading Lda"
    assert row[4] == "'" + FORMULA


@pytest.mark.requirement("REQ-EXP-005", "SEC-17")
def test_csv_separator_is_configurable_and_survives_separators_and_quotes(
    valid_environment: dict[str, str],
) -> None:
    """csv.writer escapes; a description with ; and quotes reads back as one cell."""
    valid_environment["SEXTANTE_CSV_SEPARATOR"] = ";"
    description = 'Serviço "urgente"; porto, cais 3'
    invoice = with_description(air_ticket_to_amt(), description, "QUOTES")

    rows = _csv_rows(_export(valid_environment, [invoice], FakeItemClassifier({1: "O00004"})), ";")

    assert len(rows[1]) == len(COLUMNS)
    assert rows[1][4] == description


@pytest.mark.requirement("REQ-EXP-001", "REQ-ENT-004", "L-13")
def test_ambiguous_invoice_lines_are_exported_with_empty_sheet_and_the_reason(
    valid_environment: dict[str, str],
) -> None:
    """Nothing is hidden from the reviewer: the line is there, uncoded, with why."""
    invoice = billed_to("AMBIG", "Advanced Maritime Transports Moçambique Limitada")

    row = _csv_rows(_export(valid_environment, [invoice], FakeItemClassifier()))[1]

    assert row[2:4] == ["NO", ""]
    assert (row[5], row[7]) == ("", "LOW")
    assert row[8] == "Entidade parecida com a AMT, mas não igual: confirmar."


@pytest.mark.requirement("REQ-EXP-007", "REQ-ING-002", "L-01")
def test_a_refused_document_appears_as_one_low_row_with_its_reason(
    valid_environment: dict[str, str],
) -> None:
    """Leaving the refused document out would hide that it was ever uploaded."""
    rows = _csv_rows(_export(valid_environment, [scanned_pdf_without_text()], FakeItemClassifier()))

    assert len(rows) == 2
    assert rows[1][7] == "LOW"
    assert rows[1][8] == "Documento recusado: PDF digitalizado, sem texto."


@pytest.mark.requirement("REQ-EXP-001", "REQ-ENT-008", "REQ-ING-006")
def test_notes_carry_care_of_lines_and_line_type_notes(valid_environment: dict[str, str]) -> None:
    """Care-of lines and the VAT note reach Notes_or_Flags, in Portuguese."""
    care_of = billed_to(
        "INV-002",
        "Operadora Sintética de Petróleo Angola",
        "5419990005",
        ("c/o Advanced Maritime Transports",),
    )
    vat = service_with_vat_and_discount_lines()

    rows = _csv_rows(_export(valid_environment, [care_of, vat], FakeItemClassifier({1: None})))

    assert "Ao cuidado de: c/o Advanced Maritime Transports" in rows[1][8]
    vat_row = next(row for row in rows if row[4] == "IVA 14%")
    assert (vat_row[5], vat_row[7], vat_row[8]) == ("", "HIGH", "Linha de IVA: sem código de item.")


@pytest.mark.requirement("REQ-EXP-004")
def test_export_is_built_from_persisted_state_after_a_restart(
    valid_environment: dict[str, str],
) -> None:
    """A new process with the same database exports the same rows."""
    invoice = air_ticket_to_amt()
    with running_application(
        valid_environment, [invoice], FakeItemClassifier({1: "O00004"})
    ) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        before = export_bytes(app, job_id, "csv")

    with running_application(valid_environment, [], FakeItemClassifier()) as restarted:
        after = export_bytes(restarted, job_id, "csv")

    assert after == before


@pytest.mark.requirement("SEC-16", "SEC-18", "REQ-PLT-005")
def test_export_is_an_attachment_and_an_unknown_job_is_not_found(
    valid_environment: dict[str, str],
) -> None:
    """Downloaded, never rendered; and no export for a job that does not exist."""
    invoice = air_ticket_to_amt()
    with running_application(
        valid_environment, [invoice], FakeItemClassifier({1: "O00004"})
    ) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        response = app.client.get(f"/api/exports/{job_id}", params={"format": "csv"})
        missing = app.client.get("/api/exports/nope", params={"format": "csv"})
        bad_format = app.client.get(f"/api/exports/{job_id}", params={"format": "exe"})

    assert response.headers["content-disposition"].startswith("attachment;")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert (missing.status_code, bad_format.status_code) == (404, 422)
