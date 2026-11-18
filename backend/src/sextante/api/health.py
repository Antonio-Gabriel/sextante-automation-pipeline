"""Health check endpoint."""

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict

from sextante.catalog.domain.model import Catalog

health_router = APIRouter(prefix="/api")


class HealthResponse(BaseModel):
    """Output contract of the health check (SEC-08: explicit output model)."""

    model_config = ConfigDict(frozen=True)

    status: str
    catalog_digest: str


@health_router.get("/health")
async def read_health(request: Request) -> HealthResponse:
    """Report that the process is up and which catalog version it serves.

    The digest identifies the catalog content, not a secret (D-3.9).

    Example:
        GET /api/health -> {"status": "ok", "catalog_digest": "3f2a..."}
    """
    catalog: Catalog = request.app.state.catalog
    return HealthResponse(status="ok", catalog_digest=str(catalog.digest))
