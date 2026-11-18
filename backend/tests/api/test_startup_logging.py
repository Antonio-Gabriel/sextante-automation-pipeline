"""Structured logs (NFR-OBS-001, SEC-15), observed on what the application writes to stdout."""

import json
import logging

import pytest

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
        "line_encoded", extra={"description": "Passagem aérea", "supplier_name": "companhia aérea"}
    )

    record = _json_lines(capsys.readouterr().out)[-1]
    assert record["description"] == "[redacted]"
    assert record["supplier_name"] == "[redacted]"
