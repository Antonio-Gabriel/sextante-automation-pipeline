"""List a job's lines with their coding in force, in document order (REQ-REV-001, REQ-PLT-004).

A read model that composes published readers, so that the review module reads no other
module's tables (02-arquitectura.md §2.1).
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine

from sextante.ingestion.contracts import JobLine, JobLinesReader, ReadJobStatus
from sextante.matching.contracts import exact_entity_match_label
from sextante.review.application.codings_in_force import CodingInForce, CodingsInForce


@dataclass(frozen=True, slots=True)
class ResultFilters:
    """What the reviewer narrows the queue by (REQ-REV-001). None means any."""

    confidence: str | None = None
    target_sheet: str | None = None
    flagged: bool | None = None
    invoice_id: str | None = None

    def admits(self, coding: CodingInForce | None) -> bool:
        """True when the line passes every filter that is set. An uncoded line has no values.

        Example:
            ResultFilters(confidence="LOW").admits(coding)
        """
        if self.confidence is not None and (coding is None or coding.confidence != self.confidence):
            return False
        sheet = coding.target_sheet if coding else None
        if self.target_sheet is not None and sheet != self.target_sheet:
            return False
        flagged = bool(coding and coding.flags)
        return self.flagged is None or flagged == self.flagged


@dataclass(frozen=True, slots=True)
class ResultLine:
    """One invoice line with its coding in force, as listed to the client."""

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
    flags: tuple[str, ...]
    notes: tuple[str, ...]
    review_note: str | None


class ListJobResults:
    """Return one page of a job's lines, filtered, with their coding in force.

    Example:
        lines = await ListJobResults(engine, status, lines_reader, codings).execute(
            job_id, ResultFilters(confidence="LOW"), 50, 0
        )
    """

    def __init__(
        self,
        engine: AsyncEngine,
        job_status: ReadJobStatus,
        lines_reader: JobLinesReader,
        codings: CodingsInForce,
    ) -> None:
        self._engine = engine
        self._job_status = job_status
        self._lines_reader = lines_reader
        self._codings = codings

    async def execute(
        self, job_id: str, filters: ResultFilters, limit: int, offset: int
    ) -> list[ResultLine]:
        """Return the page. Filters apply before pagination, so a page is never short of
        matches that exist further on. Lines not coded yet carry no coding.

        Example:
            await list_results.execute("3f2a...", ResultFilters(), limit=50, offset=0)

        Raises:
            JobNotFoundError: when no job has this identifier.
        """
        await self._job_status.execute(job_id)
        async with self._engine.connect() as connection:
            lines = await self._lines_reader.read_job_lines(connection, job_id, filters.invoice_id)
            codings = await self._codings.read(connection, [line.line_id for line in lines])
        admitted = [line for line in lines if filters.admits(codings.get(line.line_id))]
        page = admitted[offset : offset + limit]
        return [_result_line(line, codings.get(line.line_id)) for line in page]


def _result_line(line: JobLine, coding: CodingInForce | None) -> ResultLine:
    return ResultLine(
        invoice_id=line.invoice_id,
        invoice_line_id=line.line_id,
        encoded_line_id=coding.encoded_line_id if coding else None,
        invoice_number=line.invoice_number,
        billed_entity_detected=line.billed_entity,
        exact_entity_match=exact_entity_match_label(line.entity_verdict),
        line_position=line.position,
        line_description=line.description,
        target_sheet=coding.target_sheet if coding else None,
        item_number=coding.item_number if coding else None,
        catalog_description=coding.catalog_description if coding else None,
        confidence=coding.confidence if coding else None,
        review_status=coding.review_status if coding else None,
        flags=coding.flags if coding else (),
        notes=(coding.note,) if coding and coding.note else (),
        review_note=coding.review_note if coding else None,
    )
