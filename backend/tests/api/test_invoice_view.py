"""Frontend ticket 05: one invoice's extracted header and state (SEC-18, REQ-REV-006)."""

import time
from typing import Any, Final

import pytest

from tests.api.encoding_harness import EncodingHarness, idempotency_headers, running_application
from tests.api.test_encoding_safeguards import _query
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fixtures.synthetic_invoices import (
    air_ticket_to_amt,
    billed_to,
    reexported,
    scanned_pdf_without_text,
)

TIMEOUT_SECONDS: Final = 5.0
POLL_SECONDS: Final = 0.05
SISTER_COMPANY = "Advanced Maritime Transports Moçambique Limitada"
# The response is an explicit projection: storage details never leave the server.
FIELDS = {
    "invoice_id",
    "job_id",
    "status",
    "status_reason",
    "supplier_name",
    "supplier_nif",
    "invoice_number",
    "invoice_date",
    "currency",
    "billed_entity_detected",
    "entity_verdict",
    "entity_reason",
    "entity_resolution",
    "resolvable",
    "target_sheet",
    "possible_duplicate_of",
}


def _when_coded_again(app: EncodingHarness, invoice_id: object) -> dict[str, Any]:
    # The resolution puts the invoice back in the queue; the worker codes it shortly after.
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        body: dict[str, Any] = app.client.get(f"/api/invoices/{invoice_id}").json()
        if body["status"] not in {"queued", "not_coded"}:
            return body
        time.sleep(POLL_SECONDS)
    raise AssertionError(f"Invoice {invoice_id} was not coded again")


@pytest.mark.requirement("SEC-18", "REQ-ENT-006")
def test_an_invoice_shows_its_extracted_header_and_entity_decision(
    valid_environment: dict[str, str],
) -> None:
    """Supplier, number, date, currency, billed entity, verdict, sheet and status."""
    invoice = air_ticket_to_amt()
    with running_application(
        valid_environment, [invoice], FakeItemClassifier({1: "O00004"})
    ) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        invoice_id = app.lines(job_id)[0]["invoice_id"]
        body = app.client.get(f"/api/invoices/{invoice_id}").json()

    assert set(body) == FIELDS
    assert body | {"invoice_id": None} == {
        "invoice_id": None,
        "job_id": job_id,
        "status": "encoded",
        "status_reason": None,
        "supplier_name": "Companhia Aérea Sintética E.P.",
        "supplier_nif": "5419990001",
        "invoice_number": "SYN-2026-001",
        "invoice_date": "2026-01-12",
        "currency": "AOA",
        "billed_entity_detected": "Advanced Maritime Transports - Transitarios Limitada",
        "entity_verdict": "MATCH",
        "entity_reason": None,
        "entity_resolution": None,
        "resolvable": False,
        "target_sheet": "OUTLAYS",
        "possible_duplicate_of": None,
    }


@pytest.mark.requirement("REQ-REV-006", "D-3.15")
def test_an_ambiguous_invoice_says_why_and_can_be_resolved_once(
    valid_environment: dict[str, str],
) -> None:
    """The reason in Portuguese, resolvable until resolved, then the resolution itself."""
    invoice = billed_to("AMBIG", SISTER_COMPANY)
    # After NO_MATCH the line is coded against OUTLAYSP; the model finds no item there.
    with running_application(valid_environment, [invoice], FakeItemClassifier({1: None})) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        invoice_id = app.lines(job_id)[0]["invoice_id"]
        before = app.client.get(f"/api/invoices/{invoice_id}").json()
        app.client.post(
            f"/api/invoices/{invoice_id}/entity-resolution",
            json={"resolution": "NO_MATCH", "note": "Empresa irmã, não é a AMT."},
            headers=idempotency_headers("resolve-1"),
        )
        after = _when_coded_again(app, invoice_id)

    assert (before["entity_verdict"], before["status"], before["resolvable"]) == (
        "AMBIGUOUS",
        "not_coded",
        True,
    )
    assert before["entity_reason"]["code"] == "entity_similar_not_equal"
    # The status's reason is the entity flag, in words, never "undescribed".
    assert before["status_reason"] == before["entity_reason"]
    assert before["entity_reason"]["message"].startswith("Entidade parecida com a AMT")
    assert before["target_sheet"] is None
    assert (after["resolvable"], after["entity_reason"]) == (False, None)
    assert after["entity_resolution"]["verdict"] == "NO_MATCH"
    assert after["entity_resolution"]["note"] == "Empresa irmã, não é a AMT."
    assert after["target_sheet"] == "OUTLAYSP"


@pytest.mark.requirement("REQ-ING-011")
def test_a_possible_duplicate_names_the_earlier_invoice(
    valid_environment: dict[str, str],
) -> None:
    """The earlier invoice's identifier and number, to open it."""
    original = air_ticket_to_amt()
    copy = reexported(original, "INV-001-again")
    with running_application(
        valid_environment, [original, copy], FakeItemClassifier({1: "O00004"})
    ) as app:
        first_job = app.upload(original)["job_id"]
        app.wait_for_job(first_job)
        second_job = app.upload(copy)["job_id"]
        app.wait_for_job(second_job)
        earlier_id = app.lines(first_job)[0]["invoice_id"]
        copy_id = app.lines(second_job)[0]["invoice_id"]
        body = app.client.get(f"/api/invoices/{copy_id}").json()

    assert body["possible_duplicate_of"] == {
        "invoice_id": earlier_id,
        "invoice_number": "SYN-2026-001",
    }


@pytest.mark.requirement("REQ-ING-002", "SEC-18")
def test_a_refused_document_says_why_in_portuguese(valid_environment: dict[str, str]) -> None:
    """No header was extracted; the status and its reason are there."""
    scanned = scanned_pdf_without_text()
    with running_application(valid_environment, [scanned], FakeItemClassifier()) as app:
        job_id = app.upload(scanned)["job_id"]
        app.wait_for_job(job_id)
        # A refused document has no lines, so its identifier comes from the database.
        [(invoice_id,)] = _query(valid_environment, "SELECT id FROM invoice")
        body = app.client.get(f"/api/invoices/{invoice_id}").json()

    assert body["status"] == "rejected"
    assert body["status_reason"]["code"] == "pdf_without_text_layer"
    assert body["status_reason"]["message"]
    assert (body["supplier_name"], body["entity_verdict"], body["resolvable"]) == (
        None,
        None,
        False,
    )


@pytest.mark.requirement("SEC-18", "REQ-PLT-005")
def test_an_unknown_invoice_is_404(valid_environment: dict[str, str]) -> None:
    """The usual error body, with the Portuguese message."""
    with running_application(valid_environment, [], FakeItemClassifier()) as app:
        response = app.client.get("/api/invoices/unknown-invoice")

    assert response.status_code == 404
    assert response.json()["code"] == "errors.invoice.not_found"


@pytest.mark.requirement("REQ-PLT-002", "SEC-15")
def test_a_failed_invoice_says_it_can_be_reprocessed_without_internal_detail(
    valid_environment: dict[str, str],
) -> None:
    """The failure's exception type stays on the server; the reader gets what to do."""
    invoice = air_ticket_to_amt()
    classifier = FakeItemClassifier({1: "O00004"}, failures=[RuntimeError("model down")] * 5)
    with running_application(valid_environment, [invoice], classifier) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        [(invoice_id,)] = _query(valid_environment, "SELECT id FROM invoice")
        body = app.client.get(f"/api/invoices/{invoice_id}").json()

    assert body["status"] == "failed"
    assert body["status_reason"] == {
        "code": "processing_failed",
        "message": "Falha no processamento: a factura pode ser reprocessada.",
    }
