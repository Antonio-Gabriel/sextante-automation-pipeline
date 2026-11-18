"""HTTP API of coded results (02-arquitectura.md §6, REQ-PLT-004)."""

from typing import Annotated

from fastapi import APIRouter, Path, Query, Request
from pydantic import BaseModel, ConfigDict

from sextante.matching.infrastructure.results_query import read_job_results
from sextante.platform.limits import IDENTIFIER_MAX_LENGTH, MAX_PAGE_SIZE

matching_router = APIRouter(prefix="/api")


class ResultLineResponse(BaseModel):
    """One coded line as listed to the client (SEC-18: explicit projection)."""

    model_config = ConfigDict(frozen=True)

    invoice_number: str | None
    line_position: int
    line_description: str
    target_sheet: str | None
    item_number: str | None
    catalog_description: str | None


class ResultsPageResponse(BaseModel):
    """One page of results. ``limit_truncated`` says the requested limit was capped."""

    model_config = ConfigDict(frozen=True)

    lines: list[ResultLineResponse]
    limit: int
    offset: int
    limit_truncated: bool


@matching_router.get("/jobs/{job_id}/results", response_model=ResultsPageResponse)
async def read_results(
    request: Request,
    job_id: Annotated[str, Path(max_length=IDENTIFIER_MAX_LENGTH)],
    limit: Annotated[int, Query(ge=1)] = MAX_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ResultsPageResponse:
    """Return the job's lines in document order, paginated with a server maximum.

    Example:
        GET /api/jobs/3f2a.../results?limit=50 -> {"lines": [...], "limit": 50, ...}
    """
    page_size = min(limit, MAX_PAGE_SIZE)
    async with request.app.state.database_engine.connect() as connection:
        lines = await read_job_results(connection, job_id, page_size, offset)
    return ResultsPageResponse(
        lines=[
            ResultLineResponse(
                invoice_number=line.invoice_number,
                line_position=line.line_position,
                line_description=line.line_description,
                target_sheet=line.target_sheet,
                item_number=line.item_number,
                catalog_description=line.catalog_description,
            )
            for line in lines
        ],
        limit=page_size,
        offset=offset,
        limit_truncated=limit > MAX_PAGE_SIZE,
    )
