"""Shared test configuration: a valid environment pointing at a synthetic catalog."""

from pathlib import Path
from typing import Final

import pytest

from tests.fixtures.synthetic_catalog import SyntheticCatalog

FAKE_API_KEY: Final = "fake-test-key-not-a-secret"


@pytest.fixture
def catalog_path(tmp_path: Path) -> Path:
    """A valid synthetic catalog written to a temporary file."""
    return SyntheticCatalog().write(tmp_path / "synthetic-catalog.xlsx")


@pytest.fixture
def valid_environment(tmp_path: Path, catalog_path: Path) -> dict[str, str]:
    """Every mandatory SEXTANTE_ variable, with fictitious values (SEC-02)."""
    return {
        "SEXTANTE_ANTHROPIC_API_KEY": FAKE_API_KEY,
        "SEXTANTE_CATALOG_PATH": str(catalog_path),
        "SEXTANTE_DATABASE_URL": f"sqlite+aiosqlite:///{tmp_path / 'test-sextante.db'}",
        "SEXTANTE_TARGET_ENTITY_NAME": "Advanced Maritime Transports - Transitarios Limitada",
        "SEXTANTE_TARGET_ENTITY_NIF": "5419990000",
        "SEXTANTE_UPLOAD_DIR": str(tmp_path / "uploads"),
    }
