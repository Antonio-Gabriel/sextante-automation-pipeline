"""Ticket 02: an invoice billed to AMT is uploaded, coded against OUTLAYS, and read back."""

import pytest

from tests.api.encoding_harness import running_application
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fixtures.synthetic_invoices import hotel_stay_to_amt, taag_air_ticket_to_amt


@pytest.mark.requirement("REQ-PLT-001", "REQ-MAP-001", "REQ-MAP-003")
def test_invoice_billed_to_amt_is_coded_against_outlays_and_read_back(
    valid_environment: dict[str, str],
) -> None:
    """The tracer bullet: upload, encode in the background, read the coded line."""
    invoice = taag_air_ticket_to_amt()
    classifier = FakeItemClassifier(choices_by_item_number={1: "O00004"})

    with running_application(valid_environment, [invoice], classifier) as app:
        upload = app.upload(invoice)
        job = app.wait_for_job(upload["job_id"])
        page = app.results(upload["job_id"])

    assert job["status"] == "completed"
    assert page["lines"] == [
        {
            "invoice_number": "SYN-2026-001",
            "billed_entity_detected": "Advanced Maritime Transports - Transitarios Limitada",
            "exact_entity_match": "YES",
            "line_position": 1,
            "line_description": (
                "Passagem aérea Sintética - Rota Teste (Rotação equipa - Ref #SYN-0000001)"
            ),
            "target_sheet": "OUTLAYS",
            "item_number": "O00004",
            "catalog_description": "Bilhete Avião",
            "confidence": "MEDIUM",
            "review_status": "accepted",
            "flags": [],
            "notes": [],
        }
    ]


@pytest.mark.requirement("REQ-PLT-001")
def test_upload_answers_with_a_queued_job_before_any_coding(
    valid_environment: dict[str, str],
) -> None:
    """The upload returns at once; coding happens afterwards, in the worker."""
    invoice = taag_air_ticket_to_amt()

    with running_application(valid_environment, [invoice], FakeItemClassifier({1: None})) as app:
        upload = app.upload(invoice)

    assert upload["status"] == "queued"
    assert isinstance(upload["job_id"], str)


@pytest.mark.requirement("REQ-MAP-005", "REQ-MAP-006", "D-3.16")
def test_model_receives_the_whole_target_sheet_once_per_invoice(
    valid_environment: dict[str, str],
) -> None:
    """One call per invoice, with every OUTLAYS item in catalog order, index, code, PT, EN."""
    invoice = hotel_stay_to_amt()
    classifier = FakeItemClassifier(choices_by_item_number={1: None, 2: None})

    with running_application(valid_environment, [invoice], classifier) as app:
        app.wait_for_job(app.upload(invoice)["job_id"])

    assert len(classifier.calls) == 1
    request = classifier.calls[0]
    assert [line.position for line in request.lines] == [1, 2]
    assert [(c.index, c.item_number) for c in request.candidates] == [
        (0, "O00004"),
        (1, "O00015"),
        (2, "O00051"),
        (3, "O00052"),
        (4, "O00060"),
        (5, "O00061"),
        (6, "S00109"),
    ]
    assert (request.candidates[0].description_pt, request.candidates[0].description_en) == (
        "Bilhete Avião",
        "Air ticket",
    )


@pytest.mark.requirement("REQ-ING-004", "REQ-PLT-001")
def test_results_keep_document_order_across_lines(valid_environment: dict[str, str]) -> None:
    """Lines come back in the order in which they appear on the invoice."""
    invoice = hotel_stay_to_amt()
    classifier = FakeItemClassifier(choices_by_item_number={1: "O00004", 2: "O00051"})

    with running_application(valid_environment, [invoice], classifier) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        lines = app.results(job_id)["lines"]

    assert isinstance(lines, list)
    assert [(line["line_position"], line["item_number"]) for line in lines] == [
        (1, "O00004"),
        (2, "O00051"),
    ]
