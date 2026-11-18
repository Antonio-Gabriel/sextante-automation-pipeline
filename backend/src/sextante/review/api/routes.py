"""HTTP API of coded results (02-arquitectura.md §6, REQ-PLT-004, SEC-18)."""

from typing import Annotated

from fastapi import APIRouter, Path, Query, Request
from pydantic import BaseModel, ConfigDict

from sextante.platform.limits import IDENTIFIER_MAX_LENGTH, MAX_PAGE_SIZE
from sextante.review.application.list_job_results import ListJobResults

review_router = APIRouter(prefix="/api")


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


@review_router.get("/jobs/{job_id}/results", response_model=ResultsPageResponse)
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
    list_results: ListJobResults = request.app.state.list_job_results
    lines = await list_results.execute(job_id, page_size, offset)
    return ResultsPageResponse(
        lines=[ResultLineResponse.model_validate(line, from_attributes=True) for line in lines],
        limit=page_size,
        offset=offset,
        limit_truncated=limit > MAX_PAGE_SIZE,
    )
