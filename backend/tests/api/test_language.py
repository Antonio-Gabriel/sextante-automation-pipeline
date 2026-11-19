"""Decision 3.25: the API answers in English by default, in Portuguese on request."""

import csv
import io

import pytest

from tests.api.encoding_harness import export_bytes, running_application
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fixtures.synthetic_invoices import air_ticket_to_amt, billed_to

CHEVRON = ("INV-004", "Petrolífera Sintética de Cabinda Lda", "5419990003")


@pytest.mark.requirement("REQ-PLT-006", "REQ-PLT-005", "D-3.25")
@pytest.mark.parametrize(
    ("language", "message"), [("en", "Job not found."), ("pt", "Trabalho não encontrado.")]
)
def test_an_error_answers_in_the_language_asked(
    valid_environment: dict[str, str], language: str, message: str
) -> None:
    """Same code, the message in the request's language."""
    with running_application(valid_environment, [], FakeItemClassifier(), language=language) as app:
        body = app.client.get("/api/jobs/unknown-job").json()

    assert (body["code"], body["message"]) == ("errors.job.not_found", message)


@pytest.mark.requirement("REQ-PLT-006", "D-3.25")
def test_without_accept_language_the_answer_is_english(valid_environment: dict[str, str]) -> None:
    """English is the default, for programs and people alike."""
    with running_application(valid_environment, [], FakeItemClassifier()) as app:
        del app.client.headers["Accept-Language"]
        body = app.client.get("/api/jobs/unknown-job").json()

    assert body["message"] == "Job not found."


@pytest.mark.requirement("REQ-PLT-006", "REQ-CNF-004", "D-3.25")
def test_results_show_flags_and_the_catalog_description_in_english(
    valid_environment: dict[str, str],
) -> None:
    """The flag's text and Description 2 of the catalog; codes never change."""
    invoice = billed_to(*CHEVRON)
    with running_application(
        valid_environment, [invoice], FakeItemClassifier({1: None}), language="en"
    ) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        [line] = app.lines(job_id)

    assert line["item_number"] == "O00999"
    assert line["catalog_description"] == "Invoice under the client's name"
    assert line["flags"] == [
        {
            "code": "fallback_applied",
            "message": "No item fits: fallback O00999 (OUTLAYSP) assigned.",
        }
    ]


@pytest.mark.requirement("REQ-PLT-006", "REQ-EXP-001", "D-3.25")
def test_the_export_follows_the_language_and_keeps_its_column_names(
    valid_environment: dict[str, str],
) -> None:
    """English description and notes; the nine column names are those of the brief."""
    invoice = billed_to(*CHEVRON)
    with running_application(
        valid_environment, [invoice], FakeItemClassifier({1: None}), language="en"
    ) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        content = export_bytes(app, job_id, "csv")

    header, row = list(csv.reader(io.StringIO(content.decode("utf-8-sig"))))[:2]
    columns = dict(zip(header, row, strict=True))
    assert "Matched_Catalog_Description" in columns
    assert columns["Matched_Catalog_Description"] == "Invoice under the client's name"
    assert "No item fits: fallback O00999 (OUTLAYSP) assigned." in columns["Notes_or_Flags"]


@pytest.mark.requirement("REQ-PLT-006", "D-3.25")
def test_a_line_review_answers_the_description_in_the_language(
    valid_environment: dict[str, str],
) -> None:
    """The correction is recorded once; each answer shows it in its own language."""
    invoice = air_ticket_to_amt()
    with running_application(
        valid_environment, [invoice], FakeItemClassifier({1: "O00004"}), language="en"
    ) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        [line] = app.lines(job_id)
        history_url = f"/api/invoices/{line['invoice_id']}/lines/{line['invoice_line_id']}/history"
        english = app.client.get(history_url).json()[0]["catalog_description"]
        portuguese = app.client.get(history_url, headers={"Accept-Language": "pt"}).json()[0][
            "catalog_description"
        ]

    assert (english, portuguese) == ("Air ticket", "Bilhete Avião")


@pytest.mark.requirement("REQ-PLT-006", "REQ-PLT-005", "SEC-15")
@pytest.mark.parametrize(
    ("language", "status", "path", "code", "message"),
    [
        ("pt", 422, "/api/jobs?limit=0", "errors.request.invalid", "O pedido é inválido"),
        ("en", 422, "/api/jobs?limit=0", "errors.request.invalid", "The request is invalid"),
        ("pt", 404, "/api/nowhere", "errors.request.not_found", "O endereço pedido não existe."),
        ("en", 404, "/api/nowhere", "errors.request.not_found", "The requested address"),
    ],
)
def test_the_framework_refusals_use_the_same_body_and_language(
    valid_environment: dict[str, str],
    language: str,
    status: int,
    path: str,
    code: str,
    message: str,
) -> None:
    """No framework detail in English: the usual body, the message in the language."""
    with running_application(valid_environment, [], FakeItemClassifier(), language=language) as app:
        response = app.client.get(path)

    body = response.json()
    assert response.status_code == status
    assert set(body) == {"code", "message", "correlation_id"}
    assert body["code"] == code
    assert body["message"].startswith(message)


@pytest.mark.requirement("REQ-PLT-006", "D-3.25")
def test_every_answer_says_it_depends_on_the_language(valid_environment: dict[str, str]) -> None:
    """Vary: Accept-Language, so no cache gives one person's language to another."""
    with running_application(valid_environment, [], FakeItemClassifier()) as app:
        listed = app.client.get("/api/jobs")
        refused = app.client.get("/api/jobs/unknown-job")

    assert "Accept-Language" in listed.headers["Vary"]
    assert "Accept-Language" in refused.headers["Vary"]
