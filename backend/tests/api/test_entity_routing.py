"""Ticket 03: entity check and routing, observed through the API (REQ-MAP-001, D-3.15)."""

from pathlib import Path

import pytest

from sextante.main import create_app
from sextante.platform.settings import StartupConfigurationError
from tests.api.encoding_harness import running_application
from tests.api.test_encoding_safeguards import _query
from tests.conftest import SYNTHETIC_DENYLISTED_SISTER
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fixtures.synthetic_invoices import billed_to, taag_air_ticket_to_amt


@pytest.mark.requirement("REQ-MAP-001", "REQ-ENT-006", "R2")
def test_invoice_billed_to_a_client_is_coded_against_outlaysp(
    valid_environment: dict[str, str],
) -> None:
    """NO_MATCH routes to OUTLAYSP, and the model sees only OUTLAYSP items."""
    invoice = billed_to("INV-004", "Petrolífera Sintética de Cabinda Lda", "5419990003")
    classifier = FakeItemClassifier({1: "O00031"})

    with running_application(valid_environment, [invoice], classifier) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        line = app.results(job_id)["lines"][0]  # type: ignore[index]

    assert [c.item_number for c in classifier.calls[0].candidates] == [
        "O00002",
        "O00010",
        "O00031",
        "O00999",
    ]
    assert (line["target_sheet"], line["item_number"]) == ("OUTLAYSP", "O00031")
    assert (line["billed_entity_detected"], line["exact_entity_match"]) == (
        "Petrolífera Sintética de Cabinda Lda",
        "NO",
    )


@pytest.mark.requirement("REQ-ENT-003", "R4")
def test_sister_company_in_the_denylist_goes_to_outlaysp(
    valid_environment: dict[str, str],
) -> None:
    """The denylist read from configuration decides before any similarity."""
    invoice = billed_to("SISTER", SYNTHETIC_DENYLISTED_SISTER)

    with running_application(valid_environment, [invoice], FakeItemClassifier({1: None})) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        line = app.results(job_id)["lines"][0]  # type: ignore[index]

    assert line["target_sheet"] == "OUTLAYSP"


@pytest.mark.requirement("REQ-ENT-004", "REQ-ENT-005", "L-13")
def test_ambiguous_invoice_is_not_coded_and_never_reaches_the_model(
    valid_environment: dict[str, str],
) -> None:
    """A name close to AMT's but not equal stays uncoded, with no target sheet."""
    invoice = billed_to("AMBIG", "Advanced Maritime Transports Moçambique Limitada")
    classifier = FakeItemClassifier({1: "O00004"})

    with running_application(valid_environment, [invoice], classifier) as app:
        job_id = app.upload(invoice)["job_id"]
        job = app.wait_for_job(job_id)
        line = app.results(job_id)["lines"][0]  # type: ignore[index]

    assert classifier.calls == []
    assert job["invoice_counts"] == {"not_coded": 1}
    assert (line["target_sheet"], line["item_number"], line["exact_entity_match"]) == (
        None,
        None,
        "NO",
    )
    assert _query(
        valid_environment, "SELECT entity_verdict, entity_reason FROM invoice_header"
    ) == [("AMBIGUOUS", "entity_similar_not_equal")]


@pytest.mark.requirement("REQ-ENT-006")
def test_invoice_billed_to_amt_reports_an_exact_entity_match(
    valid_environment: dict[str, str],
) -> None:
    """The detected entity is shown as extracted, with YES for a match."""
    invoice = taag_air_ticket_to_amt()

    with running_application(
        valid_environment, [invoice], FakeItemClassifier({1: "O00004"})
    ) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        line = app.results(job_id)["lines"][0]  # type: ignore[index]

    assert (line["billed_entity_detected"], line["exact_entity_match"]) == (
        "Advanced Maritime Transports - Transitarios Limitada",
        "YES",
    )


@pytest.mark.requirement("REQ-ENT-003", "REQ-PLT-007")
@pytest.mark.parametrize(
    "content",
    ["entities: []\n", "version: 1\nentities:\n  - kind: client\n", "version: 1\nentities: x\n"],
    ids=["no version", "entry without name", "entities not a list"],
)
def test_application_refuses_to_start_with_a_malformed_denylist(
    valid_environment: dict[str, str], tmp_path: Path, content: str
) -> None:
    """A denylist that cannot be read is a configuration error, not an empty list."""
    bad = tmp_path / "bad-denylist.yaml"
    bad.write_text(content, encoding="utf-8")
    valid_environment["SEXTANTE_ENTITY_DENYLIST_PATH"] = str(bad)

    with pytest.raises(StartupConfigurationError) as refusal:
        create_app(valid_environment)

    assert "SEXTANTE_ENTITY_DENYLIST_PATH" in str(refusal.value)


@pytest.mark.requirement("REQ-ENT-003")
def test_the_repository_denylist_has_structure_and_no_invented_content() -> None:
    """L-04: the shipped file is valid and empty until AMT gives the names."""
    from sextante.matching.infrastructure.denylist_file import read_entity_denylist

    shipped = Path(__file__).resolve().parents[3] / "config" / "entity_denylist.yaml"

    assert read_entity_denylist(shipped) == frozenset()
