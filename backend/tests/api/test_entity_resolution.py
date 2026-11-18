"""Ticket 09: a reviewer resolves an ambiguous entity (REQ-REV-006, D-3.15, SEC-19)."""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine

from sextante.platform.database import MIGRATIONS_DIRECTORY
from tests.api.encoding_harness import EncodingHarness, idempotency_headers, running_application
from tests.api.test_encoding_safeguards import _query
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fixtures.synthetic_invoices import billed_to, taag_air_ticket_to_amt, with_description

SISTER_COMPANY = "Advanced Maritime Transports Moçambique Limitada"


@contextmanager
def _ambiguous_invoice(
    environment: dict[str, str], choices: dict[int, str | None]
) -> Iterator[tuple[EncodingHarness, str, str]]:
    invoice = billed_to("AMBIG", SISTER_COMPANY)
    with running_application(environment, [invoice], FakeItemClassifier(choices)) as app:
        job_id = str(app.upload(invoice)["job_id"])
        app.wait_for_job(job_id)
        line = app.lines(job_id)[0]
        yield app, job_id, str(line["invoice_id"])


def _resolve(
    app: EncodingHarness, invoice_id: str, body: dict[str, str], key: str = "resolve-1"
) -> object:
    return app.client.post(
        f"/api/invoices/{invoice_id}/entity-resolution",
        json=body,
        headers=idempotency_headers(key),
    )


@pytest.mark.requirement("REQ-REV-006", "D-3.15")
def test_a_match_resolution_codes_the_invoice_against_outlays(
    valid_environment: dict[str, str],
) -> None:
    """The invoice is coded from its stored text, and its lines may reach HIGH."""
    with _ambiguous_invoice(valid_environment, {1: "O00004"}) as (app, job_id, invoice_id):
        response = app.client.post(
            f"/api/invoices/{invoice_id}/entity-resolution",
            json={"resolution": "MATCH", "note": "Confirmado: é a AMT, sucursal de Luanda."},
            headers=idempotency_headers("resolve-1"),
        )
        app.wait_for_job(job_id)
        [line] = app.lines(job_id)

    assert response.status_code == 202
    assert (line["target_sheet"], line["item_number"], line["exact_entity_match"]) == (
        "OUTLAYS",
        "O00004",
        "YES",
    )
    assert "entity_similar_not_equal" not in [flag["code"] for flag in line["flags"]]
    assert len(app.extractor.calls) == 1


@pytest.mark.requirement("REQ-REV-006", "R3")
def test_a_no_match_resolution_codes_the_invoice_against_outlaysp(
    valid_environment: dict[str, str],
) -> None:
    """NO_MATCH routes to OUTLAYSP, where the fallback rule applies as usual."""
    with _ambiguous_invoice(valid_environment, {1: None}) as (app, job_id, invoice_id):
        _resolve(app, invoice_id, {"resolution": "NO_MATCH", "note": "Empresa irmã."})
        app.wait_for_job(job_id)
        [line] = app.lines(job_id)

    assert (line["target_sheet"], line["item_number"], line["exact_entity_match"]) == (
        "OUTLAYSP",
        "O00999",
        "NO",
    )


@pytest.mark.requirement("REQ-REV-006", "REQ-REV-004", "REQ-AUD-002")
def test_the_resolution_is_audited_and_the_placeholder_coding_is_kept(
    valid_environment: dict[str, str],
) -> None:
    """Previous verdict, new verdict, note, author; the uncoded record is superseded, not lost."""
    with _ambiguous_invoice(valid_environment, {1: "O00004"}) as (app, job_id, invoice_id):
        _resolve(app, invoice_id, {"resolution": "MATCH", "note": "Confirmado."})
        app.wait_for_job(job_id)

    [(payload_text, author)] = _query(
        valid_environment,
        "SELECT payload, author FROM audit_event WHERE event_type = 'entity_resolved'",
    )
    assert json.loads(str(payload_text)) == {
        "previous_verdict": "AMBIGUOUS",
        "previous_reason": "entity_similar_not_equal",
        "new_verdict": "MATCH",
        "note": "Confirmado.",
    }
    assert author == "synthetic-reviewer"
    assert _query(
        valid_environment,
        "SELECT target_sheet, superseded_at IS NOT NULL FROM encoded_line ORDER BY encoded_at",
    ) == [(None, 1), ("OUTLAYS", 0)]


@pytest.mark.requirement("REQ-REV-006")
def test_only_an_ambiguous_invoice_can_be_resolved(valid_environment: dict[str, str]) -> None:
    """An invoice whose entity was decided by the rules is refused."""
    invoice = taag_air_ticket_to_amt()
    with running_application(
        valid_environment, [invoice], FakeItemClassifier({1: "O00004"})
    ) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        invoice_id = str(app.results(job_id)["lines"][0]["invoice_id"])  # type: ignore[index]
        response = _resolve(app, invoice_id, {"resolution": "NO_MATCH", "note": "Não."})
        unknown = _resolve(app, "nope", {"resolution": "MATCH", "note": "x"}, key="r-2")

    assert (response.status_code, unknown.status_code) == (409, 404)  # type: ignore[attr-defined]
    assert response.json()["code"] == "errors.entity.not_ambiguous"  # type: ignore[attr-defined]


@pytest.mark.requirement("REQ-REV-006", "SEC-19")
def test_resolving_twice_codes_the_invoice_once(valid_environment: dict[str, str]) -> None:
    """The same key replays the answer; a new key finds the invoice no longer ambiguous."""
    with _ambiguous_invoice(valid_environment, {1: "O00004"}) as (app, job_id, invoice_id):
        body = {"resolution": "MATCH", "note": "Confirmado."}
        first = _resolve(app, invoice_id, body)
        repeated = _resolve(app, invoice_id, body)
        app.wait_for_job(job_id)
        again = _resolve(app, invoice_id, body, key="resolve-2")
        app.wait_for_job(job_id)

    statuses = [r.status_code for r in (first, repeated, again)]  # type: ignore[attr-defined]
    assert statuses == [202, 202, 409]
    assert _query(valid_environment, "SELECT count(*) FROM model_call") == [(1,)]


@pytest.mark.requirement("REQ-REV-006", "SEC-08")
@pytest.mark.parametrize(
    "body",
    [
        {"resolution": "MATCH"},
        {"resolution": "MATCH", "note": "   "},
        {"resolution": "MATCH", "note": "x" * 501},
        {"resolution": "AMBIGUOUS", "note": "x"},
        {"resolution": "MATCH", "note": "x", "target_sheet": "OUTLAYS"},
    ],
    ids=["no note", "blank note", "note too long", "not a resolution", "control field"],
)
def test_a_resolution_outside_the_contract_is_refused(
    valid_environment: dict[str, str], body: dict[str, str]
) -> None:
    """The note is mandatory and bounded; only MATCH or NO_MATCH; no control fields."""
    with _ambiguous_invoice(valid_environment, {1: "O00004"}) as (app, _, invoice_id):
        response = _resolve(app, invoice_id, body)

    assert response.status_code == 422  # type: ignore[attr-defined]


@pytest.mark.requirement("REQ-REV-006", "REQ-ENT-003")
def test_a_resolution_changes_neither_the_denylist_nor_the_next_check(
    valid_environment: dict[str, str],
) -> None:
    """The next invoice from the same entity is ambiguous again: the human decided once."""
    denylist = Path(valid_environment["SEXTANTE_ENTITY_DENYLIST_PATH"])
    before = denylist.read_bytes()
    first, second = billed_to("AMBIG", SISTER_COMPANY), billed_to("AMBIG-2", SISTER_COMPANY)
    with running_application(
        valid_environment, [first, second], FakeItemClassifier({1: "O00004"})
    ) as app:
        job_id = app.upload(first)["job_id"]
        app.wait_for_job(job_id)
        invoice_id = str(app.results(job_id)["lines"][0]["invoice_id"])  # type: ignore[index]
        _resolve(app, invoice_id, {"resolution": "MATCH", "note": "Confirmado."})
        app.wait_for_job(job_id)
        next_job = app.upload(second)["job_id"]
        app.wait_for_job(next_job)
        [line] = app.lines(next_job)

    assert denylist.read_bytes() == before
    assert line["target_sheet"] is None


@pytest.mark.requirement("REQ-REV-006", "REQ-CNF-001")
def test_a_resolved_invoice_is_not_capped_and_can_reach_high(
    valid_environment: dict[str, str],
) -> None:
    """The human decision lifts the entity doubt: the confidence rule applies unchanged."""
    invoice = with_description(billed_to("AMBIG-HIGH", SISTER_COMPANY), "Bilhete Avião", "hi")
    with running_application(
        valid_environment, [invoice], FakeItemClassifier({1: "O00004"})
    ) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        invoice_id = str(app.lines(job_id)[0]["invoice_id"])
        _resolve(app, invoice_id, {"resolution": "MATCH", "note": "Confirmado."})
        app.wait_for_job(job_id)
        [line] = app.lines(job_id)

    assert (line["confidence"], line["flags"], line["review_status"]) == ("HIGH", [], "accepted")


@pytest.mark.requirement("REQ-REV-006", "REQ-AUD-002")
def test_migration_0007_goes_down_with_superseded_codings(
    valid_environment: dict[str, str],
) -> None:
    """Reverting the change needs no hand work, even after a resolution (CHANGELOG rule)."""
    with _ambiguous_invoice(valid_environment, {1: "O00004"}) as (app, job_id, invoice_id):
        _resolve(app, invoice_id, {"resolution": "MATCH", "note": "Confirmado."})
        app.wait_for_job(job_id)

    url = valid_environment["SEXTANTE_DATABASE_URL"].replace("+aiosqlite", "")
    engine = create_engine(url)
    with engine.begin() as connection:
        config = Config()
        config.set_main_option("script_location", str(MIGRATIONS_DIRECTORY))
        config.attributes["connection"] = connection
        command.downgrade(config, "0006")
    engine.dispose()

    assert _query(valid_environment, "SELECT count(*), target_sheet FROM encoded_line") == [
        (1, "OUTLAYS")
    ]
