"""Frontend ticket 07: list jobs, delete a finished one softly, restore it by uploading."""

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Final

import pytest
from sqlalchemy import create_engine, text

from tests.api.encoding_harness import EncodingHarness, idempotency_headers, running_application
from tests.api.test_encoding_safeguards import _database_file, _query
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fixtures.synthetic_invoices import (
    air_ticket_to_amt,
    billed_to,
    hotel_stay_to_amt,
    reexported,
)

JOB_FIELDS: Final = {
    "job_id",
    "status",
    "created_at",
    "finished_at",
    "invoice_counts",
    "invoice_total",
}


def _delete(app: EncodingHarness, job_id: object, key: str = "delete-1") -> Any:
    return app.client.delete(f"/api/jobs/{job_id}", headers=idempotency_headers(key))


def _set_job_status(environment: dict[str, str], job_id: object, status: str) -> None:
    engine = create_engine(f"sqlite:///{_database_file(environment)}")
    try:
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE job SET status = :status WHERE id = :id"),
                {"status": status, "id": job_id},
            )
    finally:
        engine.dispose()


@pytest.mark.requirement("REQ-PLT-009", "REQ-PLT-004", "SEC-18")
def test_jobs_are_listed_newest_first_with_their_invoices(
    valid_environment: dict[str, str],
) -> None:
    """Date, status and invoices by status, no file name; the limit is capped."""
    first, second = air_ticket_to_amt(), hotel_stay_to_amt()
    classifier = FakeItemClassifier({1: "O00004"})
    with running_application(valid_environment, [first, second], classifier) as app:
        first_job = app.upload(first)["job_id"]
        app.wait_for_job(first_job)
        second_job = app.upload(second)["job_id"]
        app.wait_for_job(second_job)
        body = app.client.get("/api/jobs", params={"limit": 10_000}).json()

    assert [job["job_id"] for job in body["jobs"]] == [second_job, first_job]
    assert set(body["jobs"][0]) == JOB_FIELDS
    assert body["jobs"][0]["status"] == "completed"
    assert (body["jobs"][0]["invoice_counts"], body["jobs"][0]["invoice_total"]) == (
        {"encoded": 1},
        1,
    )
    assert (body["limit"], body["offset"], body["limit_truncated"]) == (100, 0, True)


@pytest.mark.requirement("REQ-PLT-009", "REQ-AUD-002")
def test_a_deleted_job_leaves_every_read_and_action(valid_environment: dict[str, str]) -> None:
    """The list, the job, its results, export, invoice and lines answer as if unknown."""
    invoice = air_ticket_to_amt()
    with running_application(
        valid_environment, [invoice], FakeItemClassifier({1: "O00004"})
    ) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        [line] = app.lines(job_id)
        deleted = _delete(app, job_id)
        listed = app.client.get("/api/jobs").json()["jobs"]
        invoice_url = f"/api/invoices/{line['invoice_id']}"
        line_url = f"{invoice_url}/lines/{line['invoice_line_id']}"
        statuses = [
            app.client.get(f"/api/jobs/{job_id}").status_code,
            app.client.get(f"/api/jobs/{job_id}/results").status_code,
            app.client.get(f"/api/exports/{job_id}", params={"format": "csv"}).status_code,
            app.client.get(invoice_url).status_code,
            app.client.get(f"{line_url}/candidates").status_code,
            app.client.get(f"{line_url}/history").status_code,
            app.client.post(
                f"{invoice_url}/reprocess", headers=idempotency_headers("r-1")
            ).status_code,
            app.client.post(
                f"/api/encoded-lines/{line['encoded_line_id']}/accept",
                json={},
                headers=idempotency_headers("a-1"),
            ).status_code,
            app.client.patch(
                f"/api/encoded-lines/{line['encoded_line_id']}",
                json={"item_number": "O00004"},
                headers=idempotency_headers("c-1"),
            ).status_code,
        ]

    assert (deleted.status_code, deleted.json()) == (200, {"job_id": job_id})
    assert listed == []
    assert statuses == [404] * len(statuses)
    events = _query(
        valid_environment, "SELECT subject_id FROM audit_event WHERE event_type = 'job_deleted'"
    )
    assert events == [(job_id,)]
    # Soft: the rows stay.
    assert _query(valid_environment, "SELECT count(*) FROM invoice_line") == [(1,)]


@pytest.mark.requirement("REQ-PLT-009", "SEC-19")
def test_deleting_again_changes_nothing(valid_environment: dict[str, str]) -> None:
    """The same key replays the answer; a new key finds it deleted and records nothing."""
    invoice = air_ticket_to_amt()
    with running_application(
        valid_environment, [invoice], FakeItemClassifier({1: "O00004"})
    ) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        answers = [_delete(app, job_id), _delete(app, job_id), _delete(app, job_id, "delete-2")]

    assert [a.status_code for a in answers] == [200, 200, 200]
    events = _query(
        valid_environment, "SELECT count(*) FROM audit_event WHERE event_type = 'job_deleted'"
    )
    assert events == [(1,)]


@pytest.mark.requirement("REQ-PLT-009", "REQ-PLT-005")
@pytest.mark.parametrize("status", ["queued", "running"])
def test_a_job_not_finished_is_not_deleted(valid_environment: dict[str, str], status: str) -> None:
    """409 with the Portuguese message; the job stays listed."""
    invoice = air_ticket_to_amt()
    with running_application(
        valid_environment, [invoice], FakeItemClassifier({1: "O00004"})
    ) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        _set_job_status(valid_environment, job_id, status)
        refused = _delete(app, job_id)
        listed = [job["job_id"] for job in app.client.get("/api/jobs").json()["jobs"]]

    assert refused.status_code == 409
    assert refused.json()["code"] == "errors.job.not_deletable"
    assert refused.json()["message"].startswith("Só um trabalho terminado")
    assert listed == [job_id]


@pytest.mark.requirement("REQ-PLT-009", "REQ-PLT-005")
def test_an_unknown_job_is_404(valid_environment: dict[str, str]) -> None:
    """The usual error body."""
    with running_application(valid_environment, [], FakeItemClassifier()) as app:
        response = _delete(app, "unknown-job")

    assert (response.status_code, response.json()["code"]) == (404, "errors.job.not_found")


@pytest.mark.requirement("REQ-PLT-009", "REQ-ING-007")
def test_uploading_a_file_of_a_deleted_job_restores_it_with_its_reviews(
    valid_environment: dict[str, str],
) -> None:
    """The same job comes back, not a new one: no second coding, the review kept."""
    invoice = air_ticket_to_amt()
    classifier = FakeItemClassifier({1: "O00004"})
    with running_application(valid_environment, [invoice], classifier) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        [line] = app.lines(job_id)
        app.client.post(
            f"/api/encoded-lines/{line['encoded_line_id']}/accept",
            json={},
            headers=idempotency_headers("a-1"),
        )
        _delete(app, job_id)
        again = app.upload(invoice)
        [restored_line] = app.lines(job_id)
        listed = [job["job_id"] for job in app.client.get("/api/jobs").json()["jobs"]]

    assert again["job_id"] == job_id
    assert (again["existing_job_ids"], again["restored_job_ids"]) == ([job_id], [job_id])
    assert again["status"] == "completed"
    assert restored_line["review_status"] == "accepted"
    assert listed == [job_id]
    events = _query(
        valid_environment, "SELECT subject_id FROM audit_event WHERE event_type = 'job_restored'"
    )
    assert events == [(job_id,)]


@pytest.mark.requirement("REQ-PLT-009", "REQ-ING-007")
def test_an_upload_of_a_file_of_a_job_not_deleted_restores_nothing(
    valid_environment: dict[str, str],
) -> None:
    """The usual answer of a repeated upload, with an empty list of restored jobs."""
    invoice = air_ticket_to_amt()
    with running_application(
        valid_environment, [invoice], FakeItemClassifier({1: "O00004"})
    ) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        again = app.upload(invoice)

    assert (again["job_id"], again["restored_job_ids"]) == (job_id, [])


@pytest.mark.requirement("REQ-PLT-009", "REQ-REV-006")
def test_an_ambiguous_invoice_of_a_deleted_job_is_not_resolved(
    valid_environment: dict[str, str],
) -> None:
    """The resolution answers as if the invoice were unknown, and codes nothing."""
    invoice = billed_to("AMBIG", "Advanced Maritime Transports Moçambique Limitada")
    with running_application(valid_environment, [invoice], FakeItemClassifier({1: None})) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        [(invoice_id,)] = _query(valid_environment, "SELECT id FROM invoice")
        _delete(app, job_id)
        response = app.client.post(
            f"/api/invoices/{invoice_id}/entity-resolution",
            json={"resolution": "NO_MATCH", "note": "Empresa irmã."},
            headers=idempotency_headers("resolve-1"),
        )

    assert (response.status_code, response.json()["code"]) == (404, "errors.invoice.not_found")
    assert _query(valid_environment, "SELECT count(*) FROM entity_resolution") == [(0,)]


@pytest.mark.requirement("REQ-PLT-009", "SEC-19")
def test_two_deletions_at_once_delete_once(valid_environment: dict[str, str]) -> None:
    """Two requests with different keys, sent together: both answer 200, one audit event."""
    invoice = air_ticket_to_amt()
    with running_application(
        valid_environment, [invoice], FakeItemClassifier({1: "O00004"})
    ) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        with ThreadPoolExecutor(max_workers=2) as pool:
            answers = list(pool.map(lambda key: _delete(app, job_id, key), ["d-1", "d-2"]))

    assert sorted(a.status_code for a in answers) == [200, 200]
    events = _query(
        valid_environment, "SELECT count(*) FROM audit_event WHERE event_type = 'job_deleted'"
    )
    assert events == [(1,)]


@pytest.mark.requirement("REQ-PLT-009", "REQ-ING-007")
def test_an_upload_mixing_new_files_and_a_deleted_job_restores_it_and_codes_the_new(
    valid_environment: dict[str, str],
) -> None:
    """A new job holds the new file; the deleted job of the old one comes back."""
    old, new = air_ticket_to_amt(), hotel_stay_to_amt()
    classifier = FakeItemClassifier({1: "O00004"})
    with running_application(valid_environment, [old, new], classifier) as app:
        old_job = app.upload(old)["job_id"]
        app.wait_for_job(old_job)
        _delete(app, old_job)
        mixed = app.upload(old, new)
        app.wait_for_job(mixed["job_id"])
        listed = [job["job_id"] for job in app.client.get("/api/jobs").json()["jobs"]]

    assert mixed["job_id"] != old_job
    assert (mixed["existing_job_ids"], mixed["restored_job_ids"]) == ([old_job], [old_job])
    assert listed == [mixed["job_id"], old_job]


@pytest.mark.requirement("REQ-PLT-009", "REQ-ING-011")
def test_an_invoice_of_a_deleted_job_is_no_earlier_copy(valid_environment: dict[str, str]) -> None:
    """A copy uploaded after its original's job was deleted is not flagged as a duplicate."""
    original = air_ticket_to_amt()
    copy = reexported(original, "INV-001-again")
    classifier = FakeItemClassifier({1: "O00004"})
    with running_application(valid_environment, [original, copy], classifier) as app:
        first_job = app.upload(original)["job_id"]
        app.wait_for_job(first_job)
        _delete(app, first_job)
        second_job = app.upload(copy)["job_id"]
        app.wait_for_job(second_job)
        [line] = app.lines(second_job)
        body = app.client.get(f"/api/invoices/{line['invoice_id']}").json()

    assert body["possible_duplicate_of"] is None
