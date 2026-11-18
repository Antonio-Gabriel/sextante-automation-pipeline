"""Ticket 14: a coded invoice is coded again, with its history kept (NFR-REL-002, D-3.23)."""

import json
from collections.abc import Iterator
from contextlib import contextmanager

import pytest

from tests.api.encoding_harness import (
    EncodingHarness,
    export_bytes,
    idempotency_headers,
    running_application,
)
from tests.api.test_encoding_safeguards import _query
from tests.fakes.fake_item_classifier import FAKE_PROMPT_VERSION, FakeItemClassifier
from tests.fixtures.synthetic_invoices import hotel_stay_to_amt


@contextmanager
def _coded_hotel_invoice(
    environment: dict[str, str],
) -> Iterator[tuple[EncodingHarness, str, str]]:
    invoice = hotel_stay_to_amt()
    classifier = FakeItemClassifier({1: "O00004", 2: "O00051"})
    with running_application(environment, [invoice], classifier) as app:
        job_id = str(app.upload(invoice)["job_id"])
        app.wait_for_job(job_id)
        yield app, job_id, str(app.lines(job_id)[0]["invoice_id"])


def _recode(app: EncodingHarness, invoice_id: str, job_id: str, key: str = "recode-1") -> int:
    response = app.client.post(
        f"/api/invoices/{invoice_id}/reprocess", headers=idempotency_headers(key)
    )
    app.wait_for_job(job_id)
    return response.status_code


@pytest.mark.requirement("NFR-REL-002", "SEC-19", "REQ-REV-004")
def test_a_coded_invoice_is_coded_again_and_the_earlier_coding_is_kept(
    valid_environment: dict[str, str],
) -> None:
    """New result lines take over; the earlier ones stay, superseded, never overwritten."""
    with _coded_hotel_invoice(valid_environment) as (app, job_id, invoice_id):
        status = _recode(app, invoice_id, job_id)
        lines = app.lines(job_id)

    assert status == 202
    assert [line["item_number"] for line in lines] == ["O00004", "O00051"]
    assert _query(
        valid_environment,
        "SELECT superseded_at IS NOT NULL, count(*) FROM encoded_line GROUP BY 1 ORDER BY 1",
    ) == [(0, 2), (1, 2)]
    assert _query(valid_environment, "SELECT count(*) FROM model_call") == [(2,)]
    assert len(app.extractor.calls) == 1


@pytest.mark.requirement("REQ-REV-001", "REQ-EXP-004")
def test_results_candidates_and_export_show_only_the_coding_in_force(
    valid_environment: dict[str, str],
) -> None:
    """Two codings of the same lines never show twice; each line keeps its own scores."""
    with _coded_hotel_invoice(valid_environment) as (app, job_id, invoice_id):
        _recode(app, invoice_id, job_id)
        lines = app.lines(job_id)
        candidates = app.client.get(
            f"/api/invoices/{invoice_id}/lines/{lines[0]['invoice_line_id']}/candidates"
        ).json()["candidates"]
        rows = export_bytes(app, job_id, "csv").decode("utf-8-sig").splitlines()

    assert len(lines) == 2
    assert [c["rank"] for c in candidates] == list(range(1, len(candidates) + 1))
    assert len(rows) == 1 + 2


@pytest.mark.requirement("REQ-REV-004", "D-3.23")
def test_a_reviewed_line_coded_again_is_flagged_for_review_again(
    valid_environment: dict[str, str],
) -> None:
    """The earlier review stays with the earlier coding; the new coding goes back to review."""
    with _coded_hotel_invoice(valid_environment) as (app, job_id, invoice_id):
        first = app.lines(job_id)[0]
        app.client.patch(
            f"/api/encoded-lines/{first['encoded_line_id']}",
            json={"item_number": "O00051", "note": "Revisto."},
            headers=idempotency_headers("correct-before-recoding"),
        )
        _recode(app, invoice_id, job_id)
        reviewed, untouched = app.lines(job_id)

    assert [flag["code"] for flag in reviewed["flags"]] == ["review_superseded"]
    assert (reviewed["review_status"], reviewed["item_number"]) == ("pending", "O00004")
    assert [flag["code"] for flag in untouched["flags"]] == []
    assert _query(
        valid_environment,
        "SELECT r.item_number, e.superseded_at IS NOT NULL FROM line_review r "
        "JOIN encoded_line e ON e.id = r.encoded_line_id",
    ) == [("O00051", 1)]


@pytest.mark.requirement("REQ-AUD-003", "NFR-REL-002")
def test_the_recoding_is_audited_with_earlier_and_new_prompt_and_catalog(
    valid_environment: dict[str, str],
) -> None:
    """What coded the invoice before and what codes it now, side by side."""
    with _coded_hotel_invoice(valid_environment) as (app, job_id, invoice_id):
        _recode(app, invoice_id, job_id)

    [(payload_text,)] = _query(
        valid_environment, "SELECT payload FROM audit_event WHERE event_type = 'invoice_recoded'"
    )
    payload = json.loads(str(payload_text))
    [(digest,)] = _query(valid_environment, "SELECT DISTINCT catalog_digest FROM encoded_line")
    assert payload == {
        "previous_prompt_versions": [FAKE_PROMPT_VERSION],
        "previous_catalog_digests": [digest],
        "new_prompt_version": FAKE_PROMPT_VERSION,
        "new_catalog_digest": digest,
        "superseded_lines": 2,
        "reviews_flagged_again": 0,
    }


@pytest.mark.requirement("SEC-19", "NFR-REL-002")
def test_the_same_recoding_request_twice_codes_once(valid_environment: dict[str, str]) -> None:
    """The Idempotency-Key replays the answer: one more coding, not two."""
    with _coded_hotel_invoice(valid_environment) as (app, job_id, invoice_id):
        _recode(app, invoice_id, job_id, key="same")
        _recode(app, invoice_id, job_id, key="same")

    assert _query(valid_environment, "SELECT count(*) FROM model_call") == [(2,)]
