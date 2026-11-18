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


@health_router.get("/health")
async def read_health(request: Request) -> HealthResponse:
    """Report that the process is up and which catalog version it serves.

    The digest identifies the catalog content and is not a secret (D-3.9).

    Example:
        GET /api/health -> {"status": "ok", "catalog_digest": "3f2a..."}
    """
    catalog: Catalog = request.app.state.catalog
    return HealthResponse(status="ok", catalog_digest=str(catalog.digest))
