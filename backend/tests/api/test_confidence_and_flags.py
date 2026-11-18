"""Ticket 04: confidence, fallback and flags, observed through the API."""

import json

import pytest

from sextante.main import create_app
from sextante.platform.settings import StartupConfigurationError
from tests.api.encoding_harness import running_application
from tests.api.test_encoding_safeguards import _query
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fixtures.synthetic_invoices import billed_to, taag_air_ticket_to_amt

CHEVRON = ("INV-004", "Petrolífera Sintética de Cabinda Lda", "5419990003")


def _coded_line(environment: dict[str, str], invoice, classifier) -> dict[str, object]:  # type: ignore[no-untyped-def]
    with running_application(environment, [invoice], classifier) as app:
        job_id = app.upload(invoice)["job_id"]
        app.wait_for_job(job_id)
        lines = app.results(job_id)["lines"]
    assert isinstance(lines, list)
    line: dict[str, object] = lines[0]
    return line


def _flag_codes(line: dict[str, object]) -> list[object]:
    flags = line["flags"]
    assert isinstance(flags, list)
    return [flag["code"] for flag in flags]


@pytest.mark.requirement("REQ-MAP-008", "REQ-CNF-003", "R3")
def test_outlaysp_line_without_a_fitting_item_falls_back_to_o00999(
    valid_environment: dict[str, str],
) -> None:
    """The model says none; code assigns O00999 because the sheet is OUTLAYSP."""
    line = _coded_line(valid_environment, billed_to(*CHEVRON), FakeItemClassifier({1: None}))

    assert (line["item_number"], line["confidence"], line["review_status"]) == (
        "O00999",
        "LOW",
        "pending",
    )
    assert line["catalog_description"] == "Despesas faturadas com o nome do cliente"
    assert _flag_codes(line) == ["fallback_applied"]


@pytest.mark.requirement("REQ-MAP-009", "L-08")
def test_outlays_line_without_a_fitting_item_is_left_empty_and_flagged(
    valid_environment: dict[str, str],
) -> None:
    """No O00999 and no best guess in OUTLAYS: the gap goes back to a reviewer."""
    line = _coded_line(valid_environment, taag_air_ticket_to_amt(), FakeItemClassifier({1: None}))

    assert (line["item_number"], line["confidence"]) == (None, "LOW")
    assert _flag_codes(line) == ["no_match_in_outlays"]


@pytest.mark.requirement("REQ-MAP-013", "L-08")
def test_choosing_the_generic_item_is_low_and_flagged(valid_environment: dict[str, str]) -> None:
    """O00052 is a valid answer that never passes unreviewed."""
    line = _coded_line(
        valid_environment, taag_air_ticket_to_amt(), FakeItemClassifier({1: "O00052"})
    )

    assert (line["item_number"], line["confidence"]) == ("O00052", "LOW")
    assert _flag_codes(line) == ["generic_catalog_item"]


@pytest.mark.requirement("REQ-MAP-007", "REQ-CNF-003", "SEC-14")
def test_invalid_model_answer_is_low_flagged_and_without_code(
    valid_environment: dict[str, str],
) -> None:
    """A line failure, never an improvised code."""
    line = _coded_line(
        valid_environment, taag_air_ticket_to_amt(), FakeItemClassifier(raw_indexes={1: 50})
    )

    assert (line["item_number"], line["confidence"]) == (None, "LOW")
    assert _flag_codes(line) == ["model_response_invalid"]


@pytest.mark.requirement("REQ-ENT-004", "REQ-CNF-003", "L-13")
def test_lines_of_an_ambiguous_invoice_are_low_and_flagged_with_the_entity_reason(
    valid_environment: dict[str, str],
) -> None:
    """Uncoded, no sheet, LOW, pending, and the reason says why."""
    invoice = billed_to("AMBIG", "Advanced Maritime Transports Moçambique Limitada")

    line = _coded_line(valid_environment, invoice, FakeItemClassifier({1: "O00004"}))

    assert (
        line["target_sheet"],
        line["item_number"],
        line["confidence"],
        line["review_status"],
    ) == (
        None,
        None,
        "LOW",
        "pending",
    )
    assert _flag_codes(line) == ["entity_similar_not_equal"]


@pytest.mark.requirement("REQ-CNF-004", "REQ-PLT-006")
def test_every_flag_comes_with_its_portuguese_message(valid_environment: dict[str, str]) -> None:
    """The code is stable English; what the reviewer reads is Portuguese."""
    line = _coded_line(valid_environment, billed_to(*CHEVRON), FakeItemClassifier({1: None}))

    flags = line["flags"]
    assert isinstance(flags, list)
    assert flags[0]["message"] == "Nenhum item serve: atribuído o recurso O00999 (OUTLAYSP)."


@pytest.mark.requirement("REQ-REV-005", "REQ-CNF-002")
def test_an_unflagged_line_starts_accepted(valid_environment: dict[str, str]) -> None:
    """A line with no flag needs no review."""
    line = _coded_line(
        valid_environment, taag_air_ticket_to_amt(), FakeItemClassifier({1: "O00004"})
    )

    assert line["review_status"] == "accepted"
    assert line["flags"] == []


@pytest.mark.requirement("REQ-AUD-001", "D-3.8")
def test_the_audit_event_names_the_confidence_and_the_rule(
    valid_environment: dict[str, str],
) -> None:
    """Confidence, its rule and the flags are recorded with the decision."""
    _coded_line(valid_environment, billed_to(*CHEVRON), FakeItemClassifier({1: None}))

    payload = json.loads(
        str(
            _query(
                valid_environment,
                "SELECT payload FROM audit_event WHERE event_type = 'line_encoded'",
            )[0][0]
        )
    )
    assert (payload["confidence"], payload["confidence_rule"], payload["flags"]) == (
        "LOW",
        "fallback_outlaysp",
        ["fallback_applied"],
    )


@pytest.mark.requirement("REQ-MAP-013", "REQ-PLT-007")
def test_application_refuses_a_generic_item_that_is_not_in_the_catalog(
    valid_environment: dict[str, str],
) -> None:
    """A generic item list naming an unknown code is a configuration error."""
    valid_environment["SEXTANTE_GENERIC_ITEMS"] = "O00052,X99999"

    with pytest.raises(StartupConfigurationError) as refusal:
        create_app(valid_environment)

    assert "SEXTANTE_GENERIC_ITEMS" in str(refusal.value)
