"""Ticket 08: review of coded lines (REQ-REV-001 to REQ-REV-005, SEC-08, SEC-19)."""

import csv
import io
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
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fixtures.synthetic_invoices import (
    billed_to,
    hotel_stay_to_amt,
    taag_air_ticket_to_amt,
)


@contextmanager
def _coded_job(
    environment: dict[str, str], choices: dict[int, str | None]
) -> Iterator[tuple[EncodingHarness, str, list[dict[str, object]]]]:
    invoice = hotel_stay_to_amt()
    with running_application(environment, [invoice], FakeItemClassifier(choices)) as app:
        job_id = str(app.upload(invoice)["job_id"])
        app.wait_for_job(job_id)
        lines = app.results(job_id)["lines"]
        assert isinstance(lines, list)
        yield app, job_id, lines


@pytest.mark.requirement("REQ-REV-002", "REQ-REV-004", "SEC-19")
def test_a_reviewer_corrects_a_code_within_the_target_sheet(
    valid_environment: dict[str, str],
) -> None:
    """The new code is in force, the line is corrected, and the change is audited."""
    with _coded_job(valid_environment, {1: "O00052", 2: "O00004"}) as (app, job_id, lines):
        line = lines[0]
        response = app.client.patch(
            f"/api/encoded-lines/{line['encoded_line_id']}",
            json={"item_number": "O00051", "note": "Correio, não outras despesas."},
            headers=idempotency_headers("correct-1"),
        )
        after = app.results(job_id)["lines"][0]  # type: ignore[index]

    assert response.status_code == 200
    assert (after["item_number"], after["catalog_description"], after["review_status"]) == (
        "O00051",
        "Correio Express",
        "corrected",
    )
    assert after["review_note"] == "Correio, não outras despesas."
    [(payload_text, author)] = _query(
        valid_environment,
        "SELECT payload, author FROM audit_event WHERE event_type = 'line_corrected'",
    )
    payload = json.loads(str(payload_text))
    assert (payload["previous_item_number"], payload["new_item_number"], author) == (
        "O00052",
        "O00051",
        "synthetic-reviewer",
    )


@pytest.mark.requirement("REQ-REV-004", "REQ-AUD-002")
def test_a_correction_never_overwrites_the_original_coding(
    valid_environment: dict[str, str],
) -> None:
    """The coding record keeps what the system decided; the review is stored apart."""
    with _coded_job(valid_environment, {1: "O00052", 2: "O00004"}) as (app, _, lines):
        app.client.patch(
            f"/api/encoded-lines/{lines[0]['encoded_line_id']}",
            json={"item_number": "O00051"},
            headers=idempotency_headers("correct-2"),
        )

    assert ("O00052",) in _query(valid_environment, "SELECT item_number FROM encoded_line")


@pytest.mark.requirement("REQ-REV-002", "SEC-08")
@pytest.mark.parametrize(
    ("body", "status"),
    [
        ({"item_number": "O00031"}, 422),
        ({"item_number": "XX"}, 422),
        ({"item_number": "O00051", "confidence": "HIGH"}, 422),
        ({"item_number": "O00051", "target_sheet": "OUTLAYSP"}, 422),
        ({"item_number": "O00051", "note": "x" * 501}, 422),
    ],
    ids=[
        "item of the other sheet",
        "malformed code",
        "control field confidence",
        "control field sheet",
        "note too long",
    ],
)
def test_corrections_outside_the_rules_are_refused(
    valid_environment: dict[str, str], body: dict[str, str], status: int
) -> None:
    """Only items of the line's sheet, never control fields, notes within their limit."""
    with _coded_job(valid_environment, {1: "O00052", 2: "O00004"}) as (app, _, lines):
        response = app.client.patch(
            f"/api/encoded-lines/{lines[0]['encoded_line_id']}",
            json=body,
            headers=idempotency_headers("refused"),
        )

    assert response.status_code == status


@pytest.mark.requirement("REQ-REV-002", "L-13")
def test_a_line_without_target_sheet_cannot_be_corrected(valid_environment: dict[str, str]) -> None:
    """An ambiguous invoice is unblocked by resolving its entity (ticket 09), not per line."""
    invoice = billed_to("AMBIG", "Advanced Maritime Transports Moçambique Limitada")
    with running_application(valid_environment, [invoice], FakeItemClassifier()) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        line = app.results(job_id)["lines"][0]  # type: ignore[index]
        response = app.client.patch(
            f"/api/encoded-lines/{line['encoded_line_id']}",
            json={"item_number": "O00004"},
            headers=idempotency_headers("ambiguous"),
        )

    assert response.status_code == 409
    assert response.json()["code"] == "errors.review.line_without_sheet"


@pytest.mark.requirement("REQ-REV-007", "REQ-REV-005")
def test_accepting_a_pending_line_moves_it_to_accepted(valid_environment: dict[str, str]) -> None:
    """A flagged line leaves the queue without a code change."""
    with _coded_job(valid_environment, {1: "O00052", 2: "O00004"}) as (app, job_id, lines):
        assert lines[0]["review_status"] == "pending"
        response = app.client.post(
            f"/api/encoded-lines/{lines[0]['encoded_line_id']}/accept",
            json={"note": "Confirmado com o fornecedor."},
            headers=idempotency_headers("accept-1"),
        )
        after = app.results(job_id)["lines"][0]  # type: ignore[index]

    assert response.status_code == 200
    assert (after["review_status"], after["item_number"]) == ("accepted", "O00052")
    assert _query(
        valid_environment, "SELECT count(*) FROM audit_event WHERE event_type = 'line_accepted'"
    ) == [(1,)]


@pytest.mark.requirement("SEC-19")
def test_the_same_key_twice_has_one_effect_and_returns_the_same_answer(
    valid_environment: dict[str, str],
) -> None:
    """A repeated request is answered from the record, with no second audit event."""
    with _coded_job(valid_environment, {1: "O00052", 2: "O00004"}) as (app, _, lines):
        url = f"/api/encoded-lines/{lines[0]['encoded_line_id']}/accept"
        first = app.client.post(url, json={}, headers=idempotency_headers("same"))
        second = app.client.post(url, json={}, headers=idempotency_headers("same"))

    assert (first.status_code, second.status_code) == (200, 200)
    assert first.json() == second.json()
    assert _query(
        valid_environment, "SELECT count(*) FROM audit_event WHERE event_type = 'line_accepted'"
    ) == [(1,)]


@pytest.mark.requirement("SEC-19")
def test_the_same_key_with_another_body_is_refused(valid_environment: dict[str, str]) -> None:
    """Reusing a key for a different request never returns the earlier answer."""
    with _coded_job(valid_environment, {1: "O00052", 2: "O00004"}) as (app, _, lines):
        url = f"/api/encoded-lines/{lines[0]['encoded_line_id']}"
        app.client.patch(url, json={"item_number": "O00051"}, headers=idempotency_headers("k"))
        reused = app.client.patch(
            url, json={"item_number": "O00004"}, headers=idempotency_headers("k")
        )

    assert reused.status_code == 422
    assert reused.json()["code"] == "errors.idempotency.key_reused"


@pytest.mark.requirement("SEC-19")
def test_a_review_write_without_an_idempotency_key_is_refused(
    valid_environment: dict[str, str],
) -> None:
    """The key is mandatory on POST and PATCH of review."""
    with _coded_job(valid_environment, {1: "O00052", 2: "O00004"}) as (app, _, lines):
        response = app.client.post(
            f"/api/encoded-lines/{lines[0]['encoded_line_id']}/accept", json={}
        )

    assert response.status_code == 422
    assert response.json()["code"] == "errors.idempotency.key_required"


@pytest.mark.requirement("REQ-REV-001", "REQ-PLT-004")
@pytest.mark.parametrize(
    ("params", "positions"),
    [
        ({"confidence": "LOW"}, [1]),
        ({"flagged": "true"}, [1]),
        ({"target_sheet": "OUTLAYS"}, [1, 2]),
    ],
)
def test_results_can_be_filtered(
    valid_environment: dict[str, str], params: dict[str, str], positions: list[int]
) -> None:
    """Filter by confidence, flag and target sheet, to work the queue by priority."""
    with _coded_job(valid_environment, {1: "O00052", 2: "O00004"}) as (app, job_id, _):
        response = app.client.get(f"/api/jobs/{job_id}/results", params=params)

    assert [line["line_position"] for line in response.json()["lines"]] == positions


@pytest.mark.requirement("REQ-REV-001")
def test_results_can_be_filtered_by_invoice(valid_environment: dict[str, str]) -> None:
    """Only the lines of the chosen invoice."""
    first, second = taag_air_ticket_to_amt(), hotel_stay_to_amt()
    with running_application(
        valid_environment, [first, second], FakeItemClassifier({1: None, 2: None})
    ) as app:
        files = [("files", (i.file_name, i.content, "application/pdf")) for i in (first, second)]
        job_id = app.client.post("/api/invoices", files=files).json()["job_id"]
        app.wait_for_job(job_id)
        invoice_id = app.results(job_id)["lines"][0]["invoice_id"]  # type: ignore[index]
        lines = app.client.get(
            f"/api/jobs/{job_id}/results", params={"invoice_id": invoice_id}
        ).json()["lines"]

    assert {line["invoice_id"] for line in lines} == {invoice_id}
    assert len(lines) == 1


@pytest.mark.requirement("REQ-REV-001", "SEC-18", "D-3.16")
def test_candidates_are_the_whole_sheet_ordered_by_score_with_the_model_choice(
    valid_environment: dict[str, str],
) -> None:
    """The reviewer sees every item of the sheet, best first, and what the model chose."""
    with _coded_job(valid_environment, {1: "O00052", 2: "O00004"}) as (app, _, lines):
        line = lines[0]
        response = app.client.get(
            f"/api/invoices/{line['invoice_id']}/lines/{line['invoice_line_id']}/candidates"
        )

    body = response.json()
    assert body["target_sheet"] == "OUTLAYS"
    assert [c["rank"] for c in body["candidates"]] == list(range(1, 8))
    assert [c["item_number"] for c in body["candidates"] if c["chosen_by_model"]] == ["O00052"]
    assert set(body["candidates"][0]) == {
        "item_number",
        "description_pt",
        "description_en",
        "score",
        "rank",
        "chosen_by_model",
    }


@pytest.mark.requirement("REQ-EXP-004", "REQ-REV-003")
def test_the_export_shows_the_correction_and_the_review_note(
    valid_environment: dict[str, str],
) -> None:
    """The export reflects the values in force, with the reviewer's note."""
    with _coded_job(valid_environment, {1: "O00052", 2: "O00004"}) as (app, job_id, lines):
        app.client.patch(
            f"/api/encoded-lines/{lines[0]['encoded_line_id']}",
            json={"item_number": "O00051", "note": "Corrigido."},
            headers=idempotency_headers("export-correction"),
        )
        content = export_bytes(app, job_id, "csv")

    row = list(csv.reader(io.StringIO(content.decode("utf-8-sig"))))[1]
    assert (row[5], row[6]) == ("O00051", "Correio Express")
    assert row[8].endswith("Nota de revisão: Corrigido.")


@pytest.mark.requirement("REQ-REV-007")
def test_only_a_pending_line_can_be_accepted(valid_environment: dict[str, str]) -> None:
    """Accepting twice with different keys acts once; the second answers conflict."""
    with _coded_job(valid_environment, {1: "O00052", 2: "O00004"}) as (app, _, lines):
        url = f"/api/encoded-lines/{lines[0]['encoded_line_id']}/accept"
        first = app.client.post(url, json={}, headers=idempotency_headers("a-1"))
        second = app.client.post(url, json={}, headers=idempotency_headers("a-2"))

    assert (first.status_code, second.status_code) == (200, 409)
    assert second.json()["code"] == "errors.review.not_pending"


@pytest.mark.requirement("REQ-REV-001", "SEC-18")
def test_candidates_of_a_line_of_another_invoice_are_not_found(
    valid_environment: dict[str, str],
) -> None:
    """The line must belong to the invoice named in the path."""
    with _coded_job(valid_environment, {1: "O00052", 2: "O00004"}) as (app, _, lines):
        response = app.client.get(
            f"/api/invoices/someone-else/lines/{lines[0]['invoice_line_id']}/candidates"
        )
        unknown = app.client.patch(
            "/api/encoded-lines/nope",
            json={"item_number": "O00051"},
            headers=idempotency_headers("unknown"),
        )

    assert (response.status_code, unknown.status_code) == (404, 404)
