"""HTTP API of coded results (02-arquitectura.md §6, REQ-PLT-004, SEC-18)."""

from typing import Annotated

from fastapi import APIRouter, Path, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.catalog.contracts import ITEM_NUMBER_PATTERN, TargetSheet
from sextante.matching.contracts import Confidence
from sextante.platform.idempotency import JsonBody
from sextante.platform.idempotent_route import run_idempotently
from sextante.platform.limits import IDENTIFIER_MAX_LENGTH, IDENTIFIER_PATTERN, MAX_PAGE_SIZE
from sextante.platform.user_messages import USER_MESSAGES_PT
from sextante.review.application.codings_in_force import CodingInForce
from sextante.review.application.list_job_results import ListJobResults, ResultFilters, ResultLine
from sextante.review.application.read_job_progress import ReadJobProgress
from sextante.review.application.read_line_candidates import ReadLineCandidates
from sextante.review.application.review_line import ReviewLine
from sextante.review.domain.review_state import MAX_REVIEW_NOTE_LENGTH

Identifier = Annotated[str, Path(max_length=IDENTIFIER_MAX_LENGTH, pattern=IDENTIFIER_PATTERN)]
ReviewNote = Annotated[str | None, Field(max_length=MAX_REVIEW_NOTE_LENGTH)]
ITEM_NUMBER_MAX_LENGTH = 32

review_router = APIRouter(prefix="/api")


class FlagResponse(BaseModel):
    """A flag or a note: the stable code and its Portuguese text (REQ-CNF-004, REQ-PLT-006)."""

    model_config = ConfigDict(frozen=True)

    code: str
    message: str


class ResultLineResponse(BaseModel):
    """One coded line as listed to the client (SEC-18: explicit projection)."""

    model_config = ConfigDict(frozen=True)

    invoice_id: str
    invoice_line_id: str
    encoded_line_id: str | None
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
    notes: list[FlagResponse]
    review_note: str | None


class ResultsPageResponse(BaseModel):
    """One page of results. ``limit_truncated`` says the requested limit was capped."""

    model_config = ConfigDict(frozen=True)

    lines: list[ResultLineResponse]
    limit: int
    offset: int
    limit_truncated: bool


class JobProgressResponse(BaseModel):
    """Output contract of a job's progress (REQ-PLT-001, REQ-AUD-004)."""

    model_config = ConfigDict(frozen=True)

    job_id: str
    status: str
    invoice_counts: dict[str, int]
    invoice_total: int
    input_tokens: int
    output_tokens: int


@review_router.get("/jobs/{job_id}", response_model=JobProgressResponse)
async def read_job_progress(
    request: Request,
    job_id: Annotated[str, Path(max_length=IDENTIFIER_MAX_LENGTH, pattern=IDENTIFIER_PATTERN)],
) -> JobProgressResponse:
    """Return the job status, its invoices counted by status and in total, and its tokens.

    Example:
        GET /api/jobs/3f2a... -> {"status": "completed", "invoice_total": 1, ...}
    """
    read_progress: ReadJobProgress = request.app.state.read_job_progress
    progress = await read_progress.execute(job_id)
    return JobProgressResponse(
        job_id=progress.job_id,
        status=progress.status,
        invoice_counts=progress.invoice_counts,
        invoice_total=progress.invoice_total,
        input_tokens=progress.input_tokens,
        output_tokens=progress.output_tokens,
    )


@review_router.get("/jobs/{job_id}/results", response_model=ResultsPageResponse)
async def read_results(
    request: Request,
    job_id: Annotated[str, Path(max_length=IDENTIFIER_MAX_LENGTH)],
    limit: Annotated[int, Query(ge=1)] = MAX_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
    confidence: Annotated[Confidence | None, Query()] = None,
    target_sheet: Annotated[TargetSheet | None, Query()] = None,
    flagged: Annotated[bool | None, Query()] = None,
    invoice_id: Annotated[
        str | None, Query(max_length=IDENTIFIER_MAX_LENGTH, pattern=IDENTIFIER_PATTERN)
    ] = None,
) -> ResultsPageResponse:
    """Return the job's lines in document order, filtered, paginated with a server maximum.

    Example:
        GET /api/jobs/3f2a.../results?confidence=LOW&limit=50 -> {"lines": [...], ...}
    """
    page_size = min(limit, MAX_PAGE_SIZE)
    list_results: ListJobResults = request.app.state.list_job_results
    filters = ResultFilters(confidence, target_sheet, flagged, invoice_id)
    lines = await list_results.execute(job_id, filters, page_size, offset)
    return ResultsPageResponse(
        lines=[_line_response(line) for line in lines],
        limit=page_size,
        offset=offset,
        limit_truncated=limit > MAX_PAGE_SIZE,
    )


def _line_response(line: ResultLine) -> ResultLineResponse:
    # Field by field, never by reflection: the projection is what SEC-18 asks to be explicit.
    return ResultLineResponse(
        invoice_id=line.invoice_id,
        invoice_line_id=line.invoice_line_id,
        encoded_line_id=line.encoded_line_id,
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
        notes=[FlagResponse(code=c, message=USER_MESSAGES_PT[f"notes.{c}"]) for c in line.notes],
        review_note=line.review_note,
    )


class CorrectionRequest(BaseModel):
    """Input contract of a correction: an item and a note, never a control field (SEC-08)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    item_number: str = Field(max_length=ITEM_NUMBER_MAX_LENGTH, pattern=ITEM_NUMBER_PATTERN.pattern)
    note: ReviewNote = None


class AcceptanceRequest(BaseModel):
    """Input contract of an acceptance: an optional note only (SEC-08)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    note: ReviewNote = None


class ReviewResponse(BaseModel):
    """The line's values in force after the review."""

    model_config = ConfigDict(frozen=True)

    encoded_line_id: str
    target_sheet: str | None
    item_number: str | None
    catalog_description: str | None
    confidence: str
    review_status: str
    review_note: str | None


@review_router.patch("/encoded-lines/{encoded_line_id}", response_model=ReviewResponse)
async def correct_line(
    request: Request, encoded_line_id: Identifier, body: CorrectionRequest
) -> ReviewResponse:
    """Assign another item of the line's target sheet (REQ-REV-002). Needs Idempotency-Key.

    Example:
        PATCH /api/encoded-lines/3f2a... {"item_number": "O00051"} -> 200 {...}
    """
    review_line: ReviewLine = request.app.state.review_line

    async def operation(connection: AsyncConnection) -> tuple[int, JsonBody]:
        coding = await review_line.correct(connection, encoded_line_id, body.item_number, body.note)
        return 200, _review_body(coding)

    answer = await run_idempotently(request, body.model_dump(), operation)
    return ReviewResponse.model_validate(answer)


@review_router.post("/encoded-lines/{encoded_line_id}/accept", response_model=ReviewResponse)
async def accept_line(
    request: Request, encoded_line_id: Identifier, body: AcceptanceRequest
) -> ReviewResponse:
    """Accept a pending line without changing its code (REQ-REV-007). Needs Idempotency-Key.

    Example:
        POST /api/encoded-lines/3f2a.../accept {"note": "Confirmado."} -> 200 {...}
    """
    review_line: ReviewLine = request.app.state.review_line

    async def operation(connection: AsyncConnection) -> tuple[int, JsonBody]:
        coding = await review_line.accept(connection, encoded_line_id, body.note)
        return 200, _review_body(coding)

    answer = await run_idempotently(request, body.model_dump(), operation)
    return ReviewResponse.model_validate(answer)


def _review_body(coding: CodingInForce) -> JsonBody:
    return {
        "encoded_line_id": coding.encoded_line_id,
        "target_sheet": coding.target_sheet,
        "item_number": coding.item_number,
        "catalog_description": coding.catalog_description,
        "confidence": coding.confidence,
        "review_status": coding.review_status,
        "review_note": coding.review_note,
    }


class CandidateResponse(BaseModel):
    """One item of the line's target sheet, offered to the reviewer."""

    model_config = ConfigDict(frozen=True)

    item_number: str
    description_pt: str
    description_en: str
    score: float
    rank: int
    chosen_by_model: bool


class CandidatesResponse(BaseModel):
    """The line's target sheet and its items, best lexical score first."""

    model_config = ConfigDict(frozen=True)

    target_sheet: str | None
    candidates: list[CandidateResponse]


@review_router.get(
    "/invoices/{invoice_id}/lines/{invoice_line_id}/candidates", response_model=CandidatesResponse
)
async def read_candidates(
    request: Request, invoice_id: Identifier, invoice_line_id: Identifier
) -> CandidatesResponse:
    """Return every item of the line's target sheet, with the model's choice marked.

    Example:
        GET /api/invoices/3f2a.../lines/9b1c.../candidates -> {"target_sheet": "OUTLAYS", ...}
    """
    read_line_candidates: ReadLineCandidates = request.app.state.read_line_candidates
    view = await read_line_candidates.execute(invoice_id, invoice_line_id)
    return CandidatesResponse(
        target_sheet=view.target_sheet,
        candidates=[
            CandidateResponse(
                item_number=c.item_number,
                description_pt=c.description_pt,
                description_en=c.description_en,
                score=c.score,
                rank=c.rank,
                chosen_by_model=c.chosen_by_model,
            )
            for c in view.candidates
        ],
    )
