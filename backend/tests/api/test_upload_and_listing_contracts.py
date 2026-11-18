"""Upload refusals (SEC-16), pagination (REQ-PLT-004) and response projections (SEC-18)."""

from pathlib import Path

import pytest

from sextante.platform.limits import MAX_PAGE_SIZE
from tests.api.encoding_harness import running_application
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fixtures.synthetic_invoices import taag_air_ticket_to_amt


@pytest.mark.requirement("REQ-ING-001", "SEC-16")
def test_executable_renamed_to_pdf_is_refused_by_its_content(
    valid_environment: dict[str, str],
) -> None:
    """The first bytes decide the type; the extension and Content-Type are ignored."""
    with running_application(valid_environment, [], FakeItemClassifier()) as app:
        response = app.client.post(
            "/api/invoices",
            files={"files": ("invoice.pdf", b"MZ\x90\x00binary", "application/pdf")},
        )

    assert response.status_code == 415
    assert response.json()["message"] == "Formato não suportado. Só são aceites PDF e XLSX."
    assert "correlation_id" in response.json()


@pytest.mark.requirement("SEC-16", "SEC-09")
@pytest.mark.parametrize("file_name", [b"a" * 256 + b".pdf", b"invoice\x07.pdf"])
def test_file_name_too_long_or_with_control_characters_is_refused(
    valid_environment: dict[str, str], file_name: bytes
) -> None:
    """The client's name is metadata, bounded and printable, never part of a path.

    The multipart body is written by hand: a well-behaved client percent-encodes control
    characters, and the rule exists for clients that do not.
    """
    invoice = taag_air_ticket_to_amt()
    body = (
        b'--boundary\r\nContent-Disposition: form-data; name="files"; filename="'
        + file_name
        + b'"\r\nContent-Type: application/pdf\r\n\r\n'
        + invoice.content
        + b"\r\n--boundary--\r\n"
    )
    with running_application(valid_environment, [], FakeItemClassifier()) as app:
        response = app.client.post(
            "/api/invoices",
            content=body,
            headers={"Content-Type": "multipart/form-data; boundary=boundary"},
        )

    assert response.status_code == 422
    assert response.json()["code"] == "errors.upload.invalid_file_name"


@pytest.mark.requirement("SEC-16")
def test_traversal_in_the_file_name_never_reaches_the_storage_path(
    valid_environment: dict[str, str],
) -> None:
    """Stored files are named by digest only, inside the upload directory."""
    invoice = taag_air_ticket_to_amt()
    with running_application(valid_environment, [invoice], FakeItemClassifier({1: None})) as app:
        response = app.client.post(
            "/api/invoices",
            files={"files": ("../../../etc/passwd", invoice.content, "application/pdf")},
        )

    assert response.status_code == 202
    stored = list(Path(valid_environment["SEXTANTE_UPLOAD_DIR"]).iterdir())
    assert [path.suffix for path in stored] == [".pdf"]
    assert len(stored[0].stem) == 64


@pytest.mark.requirement("REQ-PLT-001", "REQ-PLT-005")
def test_unknown_job_answers_not_found_in_portuguese(valid_environment: dict[str, str]) -> None:
    """A missing job is a 404 with a Portuguese message and a correlation id."""
    with running_application(valid_environment, [], FakeItemClassifier()) as app:
        response = app.client.get("/api/jobs/does-not-exist")

    assert response.status_code == 404
    assert response.json()["message"] == "Trabalho não encontrado."


@pytest.mark.requirement("REQ-PLT-004", "SEC-18")
def test_results_limit_above_the_server_maximum_is_capped_and_says_so(
    valid_environment: dict[str, str],
) -> None:
    """An abusive limit is truncated, and the truncation is visible in the response."""
    invoice = taag_air_ticket_to_amt()
    with running_application(valid_environment, [invoice], FakeItemClassifier({1: None})) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        page = app.results(job_id, limit=MAX_PAGE_SIZE + 500)

    assert page["limit"] == MAX_PAGE_SIZE
    assert page["limit_truncated"] is True


@pytest.mark.requirement("SEC-18")
def test_responses_carry_exactly_their_declared_fields(valid_environment: dict[str, str]) -> None:
    """No storage path, digest, worker id or prompt leaks into an API response."""
    invoice = taag_air_ticket_to_amt()
    with running_application(
        valid_environment, [invoice], FakeItemClassifier({1: "O00004"})
    ) as app:
        upload = app.upload(invoice)
        job = app.wait_for_job(upload["job_id"])
        page = app.results(upload["job_id"])

    assert set(upload) == {"job_id", "status", "invoice_count", "existing_job_ids"}
    assert set(job) == {
        "job_id",
        "status",
        "invoice_counts",
        "invoice_total",
        "input_tokens",
        "output_tokens",
        "invoice_tokens",
    }
    assert set(page) == {"lines", "limit", "offset", "limit_truncated"}
    lines = page["lines"]
    assert isinstance(lines, list)
    assert set(lines[0]) == {
        "invoice_id",
        "invoice_line_id",
        "encoded_line_id",
        "invoice_number",
        "billed_entity_detected",
        "exact_entity_match",
        "line_position",
        "line_description",
        "target_sheet",
        "item_number",
        "catalog_description",
        "confidence",
        "review_status",
        "flags",
        "notes",
        "review_note",
    }
