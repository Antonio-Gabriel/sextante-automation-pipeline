"""Ticket 07: failure isolation, retries, reprocessing and token usage (REQ-PLT-001 to 003)."""

import pytest

from sextante.matching.contracts import ItemClassifierUnavailableError
from tests.api.encoding_harness import idempotency_headers, running_application
from tests.api.test_encoding_safeguards import _query
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fixtures.synthetic_invoices import (
    air_ticket_to_amt,
    billed_to,
    hotel_stay_to_amt,
    scanned_pdf_without_text,
)

AMBIGUOUS_NAME = "Advanced Maritime Transports Moçambique Limitada"


def _unavailable() -> ItemClassifierUnavailableError:
    return ItemClassifierUnavailableError("Model timed out. Expected an answer within the timeout.")


@pytest.mark.requirement("REQ-PLT-003")
def test_transient_model_failures_are_retried_with_exponential_backoff(
    valid_environment: dict[str, str],
) -> None:
    """Two timeouts, then an answer: the invoice is coded, after waiting 1 s then 2 s."""
    invoice = air_ticket_to_amt()
    classifier = FakeItemClassifier({1: "O00004"}, failures=[_unavailable(), _unavailable()])
    sleeps: list[float] = []

    with running_application(valid_environment, [invoice], classifier, sleeps) as app:
        job = app.wait_for_job(app.upload(invoice)["job_id"])

    assert job["invoice_counts"] == {"encoded": 1}
    assert (len(classifier.calls), sleeps) == (3, [1.0, 2.0])


@pytest.mark.requirement("REQ-PLT-002", "REQ-PLT-003", "NFR-REL-001")
def test_a_model_down_for_every_attempt_fails_one_invoice_and_the_job_continues(
    valid_environment: dict[str, str],
) -> None:
    """After the last attempt the invoice is failed; the next one is still coded."""
    first = air_ticket_to_amt()
    second = billed_to("INV-004", "Petrolífera Sintética de Cabinda Lda", "5419990003")
    failures = [_unavailable(), _unavailable(), _unavailable()]
    classifier = FakeItemClassifier({1: "O00031"}, failures=failures)

    with running_application(valid_environment, [first, second], classifier) as app:
        files = [("files", (i.file_name, i.content, "application/pdf")) for i in (first, second)]
        job = app.wait_for_job(app.client.post("/api/invoices", files=files).json()["job_id"])

    assert job["status"] == "completed"
    assert job["invoice_counts"] == {"encoded": 1, "failed": 1}
    assert job["invoice_total"] == 2


@pytest.mark.requirement("REQ-PLT-003", "REQ-MAP-007")
def test_a_permanent_failure_is_not_retried(valid_environment: dict[str, str]) -> None:
    """Only an unavailable model is worth another call; anything else fails at once."""
    invoice = air_ticket_to_amt()
    classifier = FakeItemClassifier({1: "O00004"}, failures=[RuntimeError("bad request")])

    with running_application(valid_environment, [invoice], classifier) as app:
        job = app.wait_for_job(app.upload(invoice)["job_id"])

    assert job["invoice_counts"] == {"failed": 1}
    assert len(classifier.calls) == 1


@pytest.mark.requirement("NFR-REL-001", "NFR-REL-002", "SEC-19")
def test_a_failed_invoice_is_reprocessed_from_its_stored_text_without_new_extraction(
    valid_environment: dict[str, str],
) -> None:
    """Reprocessing codes the stored lines again; the file is not extracted twice."""
    invoice = air_ticket_to_amt()
    failures = [_unavailable(), _unavailable(), _unavailable()]
    classifier = FakeItemClassifier({1: "O00004"}, failures=failures)

    with running_application(valid_environment, [invoice], classifier) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        [(invoice_id,)] = _query(valid_environment, "SELECT id FROM invoice")
        response = app.client.post(
            f"/api/invoices/{invoice_id}/reprocess", headers=idempotency_headers("r-1")
        )
        job = app.wait_for_job(job_id)
        repeated = app.client.post(
            f"/api/invoices/{invoice_id}/reprocess", headers=idempotency_headers("r-1")
        )
        line = app.results(job_id)["lines"][0]  # type: ignore[index]

    assert (response.status_code, repeated.status_code) == (202, 202)
    assert repeated.json() == response.json()
    assert _query(
        valid_environment,
        "SELECT count(*) FROM audit_event WHERE event_type = 'invoice_reprocess_requested'",
    ) == [(1,)]
    assert job["invoice_counts"] == {"encoded": 1}
    assert line["item_number"] == "O00004"
    assert len(app.extractor.calls) == 1


@pytest.mark.requirement("NFR-REL-001", "NFR-REL-002")
def test_only_a_failed_or_coded_invoice_can_be_reprocessed(
    valid_environment: dict[str, str],
) -> None:
    """A refused document has no text to code; an ambiguous one waits for its entity."""
    refused, ambiguous = scanned_pdf_without_text(), billed_to("AMBIG", AMBIGUOUS_NAME)

    with running_application(
        valid_environment, [refused, ambiguous], FakeItemClassifier({1: "O00004"})
    ) as app:
        app.wait_for_job(app.upload(refused, ambiguous)["job_id"])
        rows = _query(valid_environment, "SELECT status, id FROM invoice")
        statuses = {str(status): str(invoice_id) for status, invoice_id in rows}
        answers = [
            app.client.post(
                f"/api/invoices/{statuses[status]}/reprocess", headers=idempotency_headers(status)
            )
            for status in ("rejected", "not_coded")
        ]
        unknown = app.client.post(
            "/api/invoices/nope/reprocess", headers=idempotency_headers("r-unknown")
        )

    assert [a.status_code for a in answers] == [409, 409]
    assert {a.json()["code"] for a in answers} == {"errors.invoice.not_reprocessable"}
    assert unknown.status_code == 404


@pytest.mark.requirement("REQ-AUD-004", "L-12")
def test_job_status_reports_the_tokens_of_each_invoice_and_their_sum(
    valid_environment: dict[str, str],
) -> None:
    """Tokens are shown per invoice and summed per job, to measure the real cost."""
    first, second = air_ticket_to_amt(), hotel_stay_to_amt()
    classifier = FakeItemClassifier({1: "O00004", 2: "O00004"})

    with running_application(valid_environment, [first, second], classifier) as app:
        files = [("files", (i.file_name, i.content, "application/pdf")) for i in (first, second)]
        job = app.wait_for_job(app.client.post("/api/invoices", files=files).json()["job_id"])
        lines = app.results(job["job_id"])["lines"]
    assert isinstance(lines, list)
    first_id, second_id = lines[0]["invoice_id"], lines[-1]["invoice_id"]

    assert (job["input_tokens"], job["output_tokens"]) == (300, 30)
    assert job["invoice_tokens"] == {
        first_id: {"input_tokens": 100, "output_tokens": 10},
        second_id: {"input_tokens": 200, "output_tokens": 20},
    }
