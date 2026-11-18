"""Ticket 05: line types, observed through the API (REQ-ING-006, D-3.17)."""

import json

import pytest

from tests.api.encoding_harness import running_application
from tests.api.test_encoding_safeguards import _query
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fixtures.synthetic_invoices import service_with_vat_and_discount_lines


def _run(environment: dict[str, str]) -> tuple[list[dict[str, object]], FakeItemClassifier]:
    invoice = service_with_vat_and_discount_lines()
    classifier = FakeItemClassifier({1: "O00004"})
    with running_application(environment, [invoice], classifier) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        lines = app.results(job_id)["lines"]
    assert isinstance(lines, list)
    return lines, classifier


@pytest.mark.requirement("REQ-ING-006", "D-3.17")
def test_only_service_lines_are_sent_to_the_model(valid_environment: dict[str, str]) -> None:
    """VAT and discount lines never reach the classifier."""
    _, classifier = _run(valid_environment)

    assert [line.position for line in classifier.calls[0].lines] == [1]


@pytest.mark.requirement("REQ-ING-006", "REQ-CNF-003", "L-06")
@pytest.mark.parametrize(("position", "note"), [(2, "line_type_tax"), (3, "line_type_discount")])
def test_vat_and_discount_lines_are_uncoded_high_accepted_and_not_flagged(
    valid_environment: dict[str, str], position: int, note: str
) -> None:
    """The classification is certain and there is no code to get wrong."""
    lines, _ = _run(valid_environment)

    line = next(line for line in lines if line["line_position"] == position)
    assert (line["item_number"], line["confidence"], line["review_status"], line["flags"]) == (
        None,
        "HIGH",
        "accepted",
        [],
    )
    notes = line["notes"]
    assert isinstance(notes, list)
    assert [n["code"] for n in notes] == [note]


@pytest.mark.requirement("REQ-ING-006", "REQ-ING-003", "D-3.17")
def test_summary_rows_are_not_lines_and_are_kept_in_the_audit_trail(
    valid_environment: dict[str, str],
) -> None:
    """Subtotal, VAT and total under the table are recorded once, for the invoice."""
    lines, _ = _run(valid_environment)

    assert [line["line_position"] for line in lines] == [1, 2, 3]
    [(payload_text,)] = _query(
        valid_environment,
        "SELECT payload FROM audit_event WHERE event_type = 'summary_rows_extracted'",
    )
    labels = [row["label"] for row in json.loads(str(payload_text))["summary_rows"]]
    assert labels == ["Subtotal", "Tax / IVA", "TOTAL"]


@pytest.mark.requirement("REQ-ING-004", "L-16")
def test_vat_rate_of_each_line_is_kept_as_a_line_attribute(
    valid_environment: dict[str, str],
) -> None:
    """The rate is recorded, though it does not influence the choice of code yet (L-16)."""
    _run(valid_environment)

    rates = _query(
        valid_environment,
        "SELECT position, vat_rate, line_type FROM invoice_line ORDER BY position",
    )
    assert rates == [(1, "0", "service"), (2, "14", "tax"), (3, None, "discount")]
