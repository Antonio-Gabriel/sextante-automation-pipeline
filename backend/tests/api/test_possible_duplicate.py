"""Ticket 10: the same supplier and number in another file is a possible duplicate (REQ-ING-011)."""

import csv
import dataclasses
import io

import pytest

from tests.api.encoding_harness import export_bytes, idempotency_headers, running_application
from tests.api.test_encoding_safeguards import _query
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fixtures.synthetic_invoices import (
    billed_to,
    extraction_of,
    hotel_stay_to_amt,
    reexported,
    taag_air_ticket_to_amt,
    without_invoice_number,
)


def _flag_codes(line: dict[str, object]) -> list[object]:
    flags = line["flags"]
    assert isinstance(flags, list)
    return [flag["code"] for flag in flags]


@pytest.mark.requirement("REQ-ING-011", "D-3.10")
def test_a_reexported_invoice_is_coded_and_flagged_with_the_earlier_one(
    valid_environment: dict[str, str],
) -> None:
    """Coded as usual, flagged, and pointing at the invoice uploaded first."""
    original = taag_air_ticket_to_amt()
    copy = reexported(original, "INV-001-again")
    with running_application(
        valid_environment, [original, copy], FakeItemClassifier({1: "O00004"})
    ) as app:
        first_job = app.upload(original)["job_id"]
        app.wait_for_job(first_job)
        second_job = app.upload(copy)["job_id"]
        app.wait_for_job(second_job)
        [earlier] = app.lines(first_job)
        [line] = app.lines(second_job)
        content = export_bytes(app, second_job, "csv")

    assert line["item_number"] == "O00004"
    assert _flag_codes(line) == ["possible_duplicate"]
    assert line["review_status"] == "pending"
    assert line["possible_duplicate_of"] == earlier["invoice_id"]
    assert (_flag_codes(earlier), earlier["possible_duplicate_of"]) == ([], None)
    row = list(csv.reader(io.StringIO(content.decode("utf-8-sig"))))[1]
    assert "Possível duplicado de INV-001_synthetic.pdf, carregada a 18-11-2026." in row[8]


@pytest.mark.requirement("REQ-ING-011", "SEC-19")
def test_the_same_file_again_is_the_existing_job_without_a_flag(
    valid_environment: dict[str, str],
) -> None:
    """Idempotency by digest comes first: no second invoice, so nothing to flag."""
    invoice = taag_air_ticket_to_amt()
    with running_application(
        valid_environment, [invoice], FakeItemClassifier({1: "O00004"})
    ) as app:
        first = app.upload(invoice)
        app.wait_for_job(first["job_id"])
        second = app.upload(invoice)
        [line] = app.lines(first["job_id"])

    assert second["job_id"] == first["job_id"]
    assert _flag_codes(line) == []
    assert _query(valid_environment, "SELECT count(*) FROM invoice") == [(1,)]


@pytest.mark.requirement("REQ-ING-011")
def test_an_invoice_without_number_is_never_a_possible_duplicate(
    valid_environment: dict[str, str],
) -> None:
    """Two invoices of one supplier without a number are not the same invoice."""
    first = without_invoice_number(taag_air_ticket_to_amt(), "no-number-1")
    second = without_invoice_number(taag_air_ticket_to_amt(), "no-number-2")
    with running_application(
        valid_environment, [first, second], FakeItemClassifier({1: "O00004"})
    ) as app:
        job_id = app.upload(first, second)["job_id"]
        app.wait_for_job(job_id)
        lines = app.results(job_id)["lines"]
    assert isinstance(lines, list)

    assert [_flag_codes(line) for line in lines] == [[], []]


@pytest.mark.requirement("REQ-ING-011")
def test_the_same_number_from_another_supplier_is_not_a_duplicate(
    valid_environment: dict[str, str],
) -> None:
    """Two suppliers easily issue the same number (D-3.10)."""
    taag = taag_air_ticket_to_amt()
    hotel_extraction = dataclasses.replace(
        extraction_of(hotel_stay_to_amt()), invoice_number=extraction_of(taag).invoice_number
    )
    hotel = dataclasses.replace(hotel_stay_to_amt(), extraction=hotel_extraction)
    with running_application(
        valid_environment, [taag, hotel], FakeItemClassifier({1: "O00004", 2: "O00004"})
    ) as app:
        job_id = app.upload(taag, hotel)["job_id"]
        app.wait_for_job(job_id)
        lines = app.results(job_id)["lines"]
    assert isinstance(lines, list)

    assert all("possible_duplicate" not in _flag_codes(line) for line in lines)


@pytest.mark.requirement("REQ-ING-011", "REQ-REV-006")
def test_a_duplicate_coded_again_after_resolution_is_audited_once(
    valid_environment: dict[str, str],
) -> None:
    """The resolved copy keeps its flag; the detection is recorded a single time."""
    original = billed_to("DUP", "Advanced Maritime Transports Moçambique Limitada")
    copy = reexported(original, "DUP-again")
    with running_application(
        valid_environment, [original, copy], FakeItemClassifier({1: "O00004"})
    ) as app:
        app.wait_for_job(app.upload(original)["job_id"])
        job_id = app.upload(copy)["job_id"]
        app.wait_for_job(job_id)
        invoice_id = app.lines(job_id)[0]["invoice_id"]
        app.client.post(
            f"/api/invoices/{invoice_id}/entity-resolution",
            json={"resolution": "MATCH", "note": "Confirmado."},
            headers=idempotency_headers("dup-resolve"),
        )
        app.wait_for_job(job_id)
        [line] = app.lines(job_id)

    assert (line["target_sheet"], _flag_codes(line)) == ("OUTLAYS", ["possible_duplicate"])
    assert _query(
        valid_environment,
        "SELECT count(*) FROM audit_event WHERE event_type = 'possible_duplicate_detected'",
    ) == [(1,)]
