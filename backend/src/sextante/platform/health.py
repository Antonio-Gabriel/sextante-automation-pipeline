"""Health check endpoint, part of the transversal platform layer."""

from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict

from sextante.catalog.contracts import Catalog

health_router = APIRouter(prefix="/api")


class HealthResponse(BaseModel):
    """Output contract of the health check (SEC-08: explicit output model)."""

    model_config = ConfigDict(frozen=True)

    status: Literal["ok"]
    catalog_digest: str
    # The release running, "dev" outside the release pipeline; not a secret.
    version: str


@health_router.get("/health")
async def read_health(request: Request) -> HealthResponse:
    """Report that the process is up, which release it runs and which catalog it serves.

    The digest identifies the catalog content and is not a secret (D-3.9).

    Example:
        GET /api/health -> {"status": "ok", "catalog_digest": "3f2a...", "version": "1.2.0"}
    """
    catalog: Catalog = request.app.state.catalog
    version: str = request.app.state.release_version
    return HealthResponse(status="ok", catalog_digest=str(catalog.digest), version=version)
