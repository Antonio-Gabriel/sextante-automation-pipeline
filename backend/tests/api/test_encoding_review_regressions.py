"""Regressions found by the code review of ticket 02."""

import dataclasses
import json

import pytest

from sextante.matching.domain.item_choice import ItemChoiceFromModel
from sextante.platform.limits import MAX_FILES_PER_UPLOAD, MAX_SHEET_ITEMS
from tests.api.encoding_harness import running_application
from tests.api.test_encoding_safeguards import _query
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fixtures.synthetic_invoices import (
    AMT_NAME,
    SyntheticInvoice,
    air_ticket_to_amt,
    extraction_of,
    hotel_stay_to_amt,
    synthetic_pdf_bytes,
)


@pytest.mark.requirement("REQ-MAP-005")
def test_model_receives_the_invoice_context_with_the_lines(
    valid_environment: dict[str, str],
) -> None:
    """Supplier and currency travel with the lines, as context for short descriptions."""
    invoice = air_ticket_to_amt()
    classifier = FakeItemClassifier({1: "O00004"})

    with running_application(valid_environment, [invoice], classifier) as app:
        app.wait_for_job(app.upload(invoice)["job_id"])

    context = classifier.calls[0].context
    assert (context.supplier_name, context.currency) == ("Companhia Aérea Sintética E.P.", "AOA")


@pytest.mark.requirement("REQ-ING-008")
def test_billed_entity_is_normalized_before_it_is_compared(
    valid_environment: dict[str, str],
) -> None:
    """An invisible character inside the name does not stop an otherwise exact match."""
    original = air_ticket_to_amt()
    block = dataclasses.replace(
        extraction_of(original).billed_entities[0], name=AMT_NAME.replace(" Limitada", "​ Limitada")
    )
    extraction = dataclasses.replace(extraction_of(original), billed_entities=(block,))
    invoice = SyntheticInvoice(original.file_name, synthetic_pdf_bytes("zwsp"), extraction)

    with running_application(
        valid_environment, [invoice], FakeItemClassifier({1: "O00004"})
    ) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        lines = app.results(job_id)["lines"]

    assert isinstance(lines, list)
    assert lines[0]["item_number"] == "O00004"
    stored = json.loads(
        str(_query(valid_environment, "SELECT billed_entities FROM invoice_header")[0][0])
    )
    assert "​" not in stored[0]["name"]


@pytest.mark.requirement("SEC-14", "SEC-09")
def test_schema_refuses_an_index_at_the_sheet_item_ceiling() -> None:
    """The schema caps the index at MAX_SHEET_ITEMS, before the list-length check."""
    with pytest.raises(ValueError, match="less than"):
        ItemChoiceFromModel(line_position=1, candidate_index=MAX_SHEET_ITEMS)


@pytest.mark.requirement("SEC-14")
def test_an_answer_built_without_validation_is_validated_before_use(
    valid_environment: dict[str, str],
) -> None:
    """An adapter that skips the schema still cannot get an index past the ceiling in."""
    invoice = air_ticket_to_amt()
    classifier = FakeItemClassifier({1: "O00004"}, bypass_schema_with_index=MAX_SHEET_ITEMS + 5)

    with running_application(valid_environment, [invoice], classifier) as app:
        app.wait_for_job(app.upload(invoice)["job_id"])

    # An invalid answer is a failure of that line, never a code (REQ-MAP-007).
    assert _query(valid_environment, "SELECT item_number, choice_outcome FROM encoded_line") == [
        (None, "invalid_response")
    ]


@pytest.mark.requirement("REQ-AUD-001")
def test_audit_event_keeps_the_score_of_every_item_of_the_sheet(
    valid_environment: dict[str, str],
) -> None:
    """The audit trail explains the decision with all the scores, not a sample."""
    invoice = air_ticket_to_amt()
    with running_application(
        valid_environment, [invoice], FakeItemClassifier({1: "O00004"})
    ) as app:
        app.wait_for_job(app.upload(invoice)["job_id"])

    payload = json.loads(
        str(
            _query(
                valid_environment,
                "SELECT payload FROM audit_event WHERE event_type = 'line_encoded'",
            )[0][0]
        )
    )
    assert len(payload["scores"]) == 7


@pytest.mark.requirement("REQ-ING-007")
def test_mixed_upload_reports_the_existing_job_of_files_seen_before(
    valid_environment: dict[str, str],
) -> None:
    """The new job is returned, and so is the job that already holds the repeated file."""
    seen, fresh = air_ticket_to_amt(), hotel_stay_to_amt()
    with running_application(
        valid_environment, [seen, fresh], FakeItemClassifier({1: None, 2: None})
    ) as app:
        first_job = app.upload(seen)["job_id"]
        mixed = app.upload(seen, fresh)

    assert mixed["job_id"] != first_job
    assert mixed["existing_job_ids"] == [first_job]


@pytest.mark.requirement("REQ-PLT-001", "SEC-18")
def test_results_of_an_unknown_job_answer_not_found(valid_environment: dict[str, str]) -> None:
    """Results and status agree: an unknown job is a 404 on both."""
    with running_application(valid_environment, [], FakeItemClassifier()) as app:
        response = app.client.get("/api/jobs/does-not-exist/results")

    assert response.status_code == 404


@pytest.mark.requirement("SEC-16", "SEC-09")
def test_upload_with_too_many_files_is_refused(valid_environment: dict[str, str]) -> None:
    """The file count is a bounded input like any other (03-seguranca.md §9.1)."""
    files = [
        ("files", (f"f{n}.pdf", synthetic_pdf_bytes(f"many-{n}"), "application/pdf"))
        for n in range(MAX_FILES_PER_UPLOAD + 1)
    ]
    with running_application(valid_environment, [], FakeItemClassifier()) as app:
        response = app.client.post("/api/invoices", files=files)

    assert response.status_code == 422
    assert response.json()["code"] == "errors.upload.too_many_files"
