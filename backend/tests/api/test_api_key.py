"""The API is not open: every /api call but the health check needs X-API-Key (L-07, SEC-06)."""

from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from sextante.main import create_app
from sextante.platform.settings import StartupConfigurationError
from tests.conftest import SYNTHETIC_API_KEY


@contextmanager
def _client(environment: dict[str, str]) -> Iterator[TestClient]:
    # No key by default: each test sends the header it means to send.
    with TestClient(create_app(environment)) as client:
        yield client


@pytest.mark.requirement("SEC-06", "L-07")
@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "wrong-key-of-enough-length"}])
def test_a_call_without_the_right_key_is_refused(
    valid_environment: dict[str, str], headers: dict[str, str]
) -> None:
    """No key, or another key: 401, with the Portuguese message and no detail."""
    with _client(valid_environment) as client:
        response = client.get("/api/jobs/some-job", headers=headers)

    assert response.status_code == 401
    assert response.json()["code"] == "errors.auth.credential_invalid"


@pytest.mark.requirement("SEC-06", "L-07")
def test_the_right_key_lets_the_call_through(valid_environment: dict[str, str]) -> None:
    """With the configured key the request reaches the route (here, an unknown job)."""
    with _client(valid_environment) as client:
        response = client.get("/api/jobs/some-job", headers={"X-API-Key": SYNTHETIC_API_KEY})

    assert response.status_code == 404


@pytest.mark.requirement("SEC-06", "NFR-DOC-001")
def test_health_and_the_interactive_docs_stay_open(valid_environment: dict[str, str]) -> None:
    """A monitor checks health, and a person reads the docs, without the key."""
    with _client(valid_environment) as client:
        statuses = [client.get(path).status_code for path in ("/api/health", "/docs")]
        scheme = client.get("/openapi.json").json()["components"]["securitySchemes"]

    assert statuses == [200, 200]
    assert sorted((s["type"], s["in"], s["name"]) for s in scheme.values()) == [
        ("apiKey", "cookie", "sextante_session"),
        ("apiKey", "header", "X-API-Key"),
    ]


@pytest.mark.requirement("SEC-15", "SEC-06")
def test_a_refused_key_never_reaches_the_log(
    valid_environment: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    """The refusal is logged by its event only, never with the key that was sent."""
    with _client(valid_environment) as client:
        capsys.readouterr()
        client.get("/api/jobs/some-job", headers={"X-API-Key": "leaked-key-value-1234"})

    output = capsys.readouterr().out
    assert "credential_rejected" in output
    assert "leaked-key-value-1234" not in output


@pytest.mark.requirement("REQ-PLT-007", "SEC-02")
def test_a_short_api_key_refuses_startup(valid_environment: dict[str, str]) -> None:
    """A key a person could guess is refused before the server accepts a request."""
    with pytest.raises(StartupConfigurationError) as refusal:
        create_app({**valid_environment, "SEXTANTE_API_KEY": "short"})

    assert "SEXTANTE_API_KEY" in str(refusal.value)
