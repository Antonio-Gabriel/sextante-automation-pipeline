"""Application startup, observed from the outside: the app factory and the HTTP API."""

import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sextante.main import create_app
from sextante.platform.settings import StartupConfigurationError
from tests.conftest import FAKE_API_KEY


@pytest.mark.requirement("REQ-PLT-008")
def test_application_with_valid_configuration_answers_health_check(
    valid_environment: dict[str, str],
) -> None:
    """A fresh install with a complete configuration starts and reports healthy."""
    with TestClient(create_app(valid_environment)) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


MANDATORY_VARIABLES = (
    "SEXTANTE_ANTHROPIC_API_KEY",
    "SEXTANTE_CATALOG_PATH",
    "SEXTANTE_DATABASE_URL",
    "SEXTANTE_TARGET_ENTITY_NAME",
    "SEXTANTE_TARGET_ENTITY_NIF",
)


@pytest.mark.requirement("REQ-PLT-007", "SEC-02")
@pytest.mark.parametrize("missing_variable", MANDATORY_VARIABLES)
def test_application_refuses_to_start_when_mandatory_setting_is_missing(
    valid_environment: dict[str, str], missing_variable: str
) -> None:
    """Failing at startup beats discovering a missing setting during month-end close."""
    del valid_environment[missing_variable]

    with pytest.raises(StartupConfigurationError) as refusal:
        create_app(valid_environment)

    assert missing_variable in str(refusal.value)


@pytest.mark.requirement("SEC-02", "SEC-15")
def test_startup_refusal_never_echoes_the_api_key(valid_environment: dict[str, str]) -> None:
    """The refusal names what is wrong without printing secret values."""
    del valid_environment["SEXTANTE_TARGET_ENTITY_NIF"]

    with pytest.raises(StartupConfigurationError) as refusal:
        create_app(valid_environment)

    assert FAKE_API_KEY not in str(refusal.value)


@pytest.mark.requirement("REQ-PLT-007")
def test_startup_reads_only_the_environment_it_is_given(
    valid_environment: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A stray variable in the process environment cannot fill a missing setting."""
    monkeypatch.setenv("SEXTANTE_TARGET_ENTITY_NIF", "5419990000")
    del valid_environment["SEXTANTE_TARGET_ENTITY_NIF"]

    with pytest.raises(StartupConfigurationError):
        create_app(valid_environment)


@pytest.mark.requirement("REQ-MAP-011", "D-3.9")
def test_health_reports_the_digest_of_the_loaded_catalog(
    valid_environment: dict[str, str], catalog_path: Path
) -> None:
    """The catalog version in use is the SHA-256 of the file content, not its name."""
    expected_digest = hashlib.sha256(catalog_path.read_bytes()).hexdigest()

    with TestClient(create_app(valid_environment)) as client:
        response = client.get("/api/health")

    assert response.json()["catalog_digest"] == expected_digest
