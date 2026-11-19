"""Decision 3.27: the public deploy shows its release and hides the API description."""

import pytest
from fastapi.testclient import TestClient

from sextante.main import create_app
from sextante.platform.settings import StartupConfigurationError


@pytest.mark.requirement("D-3.27", "REQ-PLT-008")
def test_the_health_check_names_the_release_it_runs(valid_environment: dict[str, str]) -> None:
    """The pipeline reads it to confirm a deploy took effect; "dev" outside a release."""
    released = valid_environment | {"SEXTANTE_RELEASE_VERSION": "1.2.0"}
    with (
        TestClient(create_app(valid_environment)) as local,
        TestClient(create_app(released)) as public,
    ):
        assert local.get("/api/health").json()["version"] == "dev"
        assert public.get("/api/health").json()["version"] == "1.2.0"


@pytest.mark.requirement("D-3.27", "REQ-PLT-007")
def test_a_malformed_release_version_refuses_startup(valid_environment: dict[str, str]) -> None:
    """Only letters, digits, dots, plus and minus: nothing a header or a page could carry."""
    with pytest.raises(StartupConfigurationError, match=r"SEXTANTE_RELEASE_VERSION"):
        create_app(valid_environment | {"SEXTANTE_RELEASE_VERSION": "1.2<script>"})


@pytest.mark.requirement("D-3.27", "SEC-15")
@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_the_api_description_can_be_switched_off(
    valid_environment: dict[str, str], path: str
) -> None:
    """Open by default for local use; gone where the server is public."""
    hidden = valid_environment | {"SEXTANTE_API_DOCS_ENABLED": "false"}
    with (
        TestClient(create_app(valid_environment)) as local,
        TestClient(create_app(hidden)) as public,
    ):
        assert local.get(path).status_code == 200
        assert public.get(path).status_code == 404
