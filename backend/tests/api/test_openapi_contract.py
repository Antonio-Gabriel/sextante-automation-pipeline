"""The frontend's API types come from this OpenAPI document, never written by hand (§7).

The document is kept in the frontend folder, and this test fails when the API changes
and the copy does not: regenerate with `make openapi`, then `npm run api:types`.
"""

import json
import os
from pathlib import Path
from typing import Final

import pytest

from sextante.main import create_app

OPENAPI_COPY: Final = Path(__file__).parents[3] / "frontend" / "openapi.json"
WRITE_FLAG: Final = "OPENAPI_SNAPSHOT_WRITE"


@pytest.mark.requirement("NFR-DOC-001")
def test_the_frontend_copy_of_the_openapi_document_is_current(
    valid_environment: dict[str, str],
) -> None:
    """A changed contract reaches the frontend's generated types, or this test fails."""
    document = json.dumps(create_app(valid_environment).openapi(), indent=2, sort_keys=True)
    if os.environ.get(WRITE_FLAG) == "1":
        OPENAPI_COPY.write_text(document + "\n", encoding="utf-8")

    assert OPENAPI_COPY.read_text(encoding="utf-8") == document + "\n", (
        "frontend/openapi.json is stale. Run `make openapi`, then `npm run api:types`."
    )
