"""Structured logs (NFR-OBS-001, SEC-15), observed on what the application writes to stdout."""

import json
import logging

import pytest
from fastapi.testclient import TestClient

from sextante.main import create_app


def _json_lines(output: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in output.splitlines() if line.strip()]


@pytest.mark.requirement("NFR-OBS-001")
def test_startup_writes_one_json_object_per_log_line_with_a_correlation_id(
    valid_environment: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    """Every record is JSON on stdout, with an English snake_case event and a correlation id."""
    create_app(valid_environment)

    records = _json_lines(capsys.readouterr().out)
    warning = next(r for r in records if r["event"] == "catalog_item_warning")
    assert warning["level"] == "WARNING"
    assert warning["item_number"] in {"O00060", "O00010", "O00061"}
    assert all("correlation_id" in record for record in records)


@pytest.mark.requirement("SEC-15")
def test_forbidden_fields_are_redacted_even_when_a_developer_logs_them(
    valid_environment: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    """A redaction filter masks invoice content, so a slip does not become a leak."""
    create_app(valid_environment)
    capsys.readouterr()

    logging.getLogger("sextante.test").warning(
        "line_encoded",
        extra={"description": "Passagem aérea", "supplier_name": "Fornecedor Sintético"},
    )

    record = _json_lines(capsys.readouterr().out)[-1]
    assert record["description"] == "[redacted]"
    assert record["supplier_name"] == "[redacted]"


@pytest.mark.requirement("SEC-15")
def test_application_records_never_reach_other_handlers_unredacted(
    valid_environment: dict[str, str], caplog: pytest.LogCaptureFixture
) -> None:
    """Records stop at the application's own JSON handler, so no root handler sees raw fields."""
    create_app(valid_environment)

    with caplog.at_level(logging.WARNING):
        logging.getLogger("sextante.test").warning("line_encoded", extra={"description": "X"})

    assert caplog.records == []


@pytest.mark.requirement("NFR-OBS-001")
def test_server_records_are_json_too(
    valid_environment: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    """The server's own startup and access records follow the same JSON format."""
    create_app(valid_environment)
    capsys.readouterr()

    logging.getLogger("uvicorn.error").info("Application startup complete.")

    record = _json_lines(capsys.readouterr().out)[-1]
    assert record["event"] == "Application startup complete."
    assert "correlation_id" in record


@pytest.mark.requirement("NFR-OBS-001", "REQ-PLT-005")
def test_each_request_gets_its_own_correlation_id_in_header_and_logs(
    valid_environment: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    """The id returned to the client is the one on every record written during the request."""
    app = create_app(valid_environment)

    def log_something() -> dict[str, str]:
        logging.getLogger("sextante.test").info("probe_request_logged")
        return {}

    app.add_api_route("/api/probe", log_something)
    with TestClient(app) as client:
        first = client.get("/api/probe").headers["X-Correlation-ID"]
        second = client.get("/api/probe").headers["X-Correlation-ID"]

    probes = [
        r for r in _json_lines(capsys.readouterr().out) if r["event"] == "probe_request_logged"
    ]
    assert first != second
    assert [r["correlation_id"] for r in probes] == [first, second]


@pytest.mark.requirement("NFR-OBS-001")
def test_server_colour_codes_do_not_reach_the_json_log(
    valid_environment: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    """Terminal colour variants of a message are display noise, not log content."""
    create_app(valid_environment)
    capsys.readouterr()

    logging.getLogger("uvicorn.error").info("Started", extra={"color_message": "\x1b[36mS\x1b[0m"})

    assert "color_message" not in _json_lines(capsys.readouterr().out)[-1]
