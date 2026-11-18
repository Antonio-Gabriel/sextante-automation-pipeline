"""Ticket 12 end to end: SYNTHETIC PDFs read by the real extractor, then coded (D-3.6)."""

import csv
import io
import time
from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from sextante.main import AppDependencies, create_app
from tests.api.encoding_harness import running_application
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fakes.fixed_clock import FixedClock, SequentialIdentifierGenerator
from tests.fixtures.synthetic_invoices import AMT_NIF, taag_air_ticket_to_amt, with_description
from tests.fixtures.synthetic_pdf import (
    air_ticket_pdf,
    care_of_pdf,
    model_invoice_pdf,
    other_document_pdf,
    scanned_pdf,
)

TIMEOUT_SECONDS = 10.0


@contextmanager
def _application(
    environment: dict[str, str], choices: dict[int, str | None] | None = None
) -> Iterator[TestClient]:
    # No extractor given: the application builds the native PDF extractor itself.
    dependencies = AppDependencies(
        classifier=FakeItemClassifier(choices or {1: "O00004"}),
        clock=FixedClock(),
        identifiers=SequentialIdentifierGenerator(),
        worker_poll_seconds=0.01,
    )
    with TestClient(create_app(environment, dependencies)) as client:
        yield client


def _upload(client: TestClient, name: str, content: bytes, content_type: str) -> str:
    response = client.post("/api/invoices", files={"files": (name, content, content_type)})
    assert response.status_code == 202, response.text
    job_id = str(response.json()["job_id"])
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while client.get(f"/api/jobs/{job_id}").json()["status"] != "completed":
        assert time.monotonic() < deadline
        time.sleep(0.01)
    return job_id


@pytest.mark.requirement("REQ-ING-001", "REQ-ING-003", "SEC-16")
def test_a_pdf_is_read_by_its_bytes_whatever_its_name_or_declared_type(
    valid_environment: dict[str, str],
) -> None:
    """A PDF sent as "invoice.xlsx" with a spreadsheet type is still read as a PDF."""
    content = model_invoice_pdf(air_ticket_pdf())
    with _application(valid_environment) as client:
        job_id = _upload(client, "invoice_synthetic.xlsx", content, "application/vnd.ms-excel")
        [line] = client.get(f"/api/jobs/{job_id}/results").json()["lines"]

    assert (line["invoice_number"], line["exact_entity_match"], line["item_number"]) == (
        "SYN-2026-001",
        "YES",
        "O00004",
    )
    assert line["line_description"].endswith("(Rotação equipa - Ref #SYN-0000001)")


@pytest.mark.requirement("REQ-ING-005", "D-3.15")
def test_a_care_of_invoice_is_routed_by_its_billed_entity(
    valid_environment: dict[str, str],
) -> None:
    """ "c/o AMT" stays a note: the client is the billed entity, so OUTLAYSP."""
    content = model_invoice_pdf(care_of_pdf())
    with _application(valid_environment, {1: "O00031"}) as client:
        job_id = _upload(client, "care_of_synthetic.pdf", content, "application/pdf")
        [line] = client.get(f"/api/jobs/{job_id}/results").json()["lines"]
        export = client.get(f"/api/exports/{job_id}", params={"format": "csv"}).content

    row = list(csv.reader(io.StringIO(export.decode("utf-8-sig"))))[1]
    assert (line["billed_entity_detected"], line["target_sheet"]) == (
        "Operadora Sintética de Petróleo Angola",
        "OUTLAYSP",
    )
    assert row[0] == "5419990004/AO-SYN0002"
    assert AMT_NIF not in row[0]


@pytest.mark.requirement("REQ-ING-002", "REQ-ING-009", "REQ-EXP-007")
@pytest.mark.parametrize(
    ("content", "message"),
    [
        (scanned_pdf(), "Documento recusado: PDF digitalizado, sem texto."),
        (other_document_pdf(), "Documento recusado: não é uma factura no modelo suportado."),
    ],
    ids=["scanned", "not the model"],
)
def test_a_refused_pdf_is_never_coded_and_says_why(
    valid_environment: dict[str, str], content: bytes, message: str
) -> None:
    """No lines, no model call; the export has one row with the reason."""
    with _application(valid_environment) as client:
        job_id = _upload(client, "refused_synthetic.pdf", content, "application/pdf")
        lines = client.get(f"/api/jobs/{job_id}/results").json()["lines"]
        progress = client.get(f"/api/jobs/{job_id}").json()
        export = client.get(f"/api/exports/{job_id}", params={"format": "csv"}).content

    row = list(csv.reader(io.StringIO(export.decode("utf-8-sig"))))[1]
    assert (lines, progress["invoice_counts"], progress["input_tokens"]) == ([], {"rejected": 1}, 0)
    assert row[8] == message


@pytest.mark.requirement("REQ-ING-008", "SEC-09")
def test_extracted_text_is_stored_in_nfc_and_without_control_characters(
    valid_environment: dict[str, str],
) -> None:
    """Decomposed accents are composed and control characters dropped before persisting."""
    invoice = with_description(taag_air_ticket_to_amt(), "Café\x07 e serviço", "nfc")
    with running_application(
        valid_environment, [invoice], FakeItemClassifier({1: "O00004"})
    ) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        [line] = app.lines(job_id)

    assert line["line_description"] == "Café e serviço"
