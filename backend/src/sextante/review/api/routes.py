"""HTTP API of coded results (02-arquitectura.md §6, REQ-PLT-004, SEC-18)."""

from typing import Annotated

from fastapi import APIRouter, Path, Query, Request
from pydantic import BaseModel, ConfigDict

from sextante.platform.limits import IDENTIFIER_MAX_LENGTH, MAX_PAGE_SIZE
from sextante.platform.user_messages import USER_MESSAGES_PT
from sextante.review.application.list_job_results import ListJobResults, ResultLine

review_router = APIRouter(prefix="/api")


class FlagResponse(BaseModel):
    """One flag: the stable code and the Portuguese text shown to the reviewer (REQ-CNF-004)."""

    model_config = ConfigDict(frozen=True)

    code: str
    message: str


class ResultLineResponse(BaseModel):
    """One coded line as listed to the client (SEC-18: explicit projection)."""

    model_config = ConfigDict(frozen=True)

    invoice_number: str | None
    billed_entity_detected: str | None
    exact_entity_match: str
    line_position: int
    line_description: str
    target_sheet: str | None
    item_number: str | None
    catalog_description: str | None
    confidence: str | None
    review_status: str | None
    flags: list[FlagResponse]


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
        lines=[_line_response(line) for line in lines],
        limit=page_size,
        offset=offset,
        limit_truncated=limit > MAX_PAGE_SIZE,
    )


def _line_response(line: ResultLine) -> ResultLineResponse:
    # Field by field, never by reflection: the projection is what SEC-18 asks to be explicit.
    return ResultLineResponse(
        invoice_number=line.invoice_number,
        billed_entity_detected=line.billed_entity_detected,
        exact_entity_match=line.exact_entity_match,
        line_position=line.line_position,
        line_description=line.line_description,
        target_sheet=line.target_sheet,
        item_number=line.item_number,
        catalog_description=line.catalog_description,
        confidence=line.confidence,
        review_status=line.review_status,
        flags=[FlagResponse(code=c, message=USER_MESSAGES_PT[f"flags.{c}"]) for c in line.flags],
    )
