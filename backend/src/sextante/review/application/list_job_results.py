"""List a job's lines with their coding, in document order (REQ-REV-001, REQ-PLT-004).

A read model that composes two published readers, so that neither module reads the
other's tables (02-arquitectura.md §2.1).
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine

from sextante.ingestion.contracts import JobLinesReader, ReadJobStatus
from sextante.matching.contracts import CodingsReader


@dataclass(frozen=True, slots=True)
class ResultLine:
    """One invoice line with its coding, as listed to the client."""

    invoice_number: str | None
    line_position: int
    line_description: str
    target_sheet: str | None
    item_number: str | None
    catalog_description: str | None


class ListJobResults:
    """Return one page of a job's lines with their coding.

    Example:
        lines = await ListJobResults(engine, status, lines_reader, codings).execute(job_id, 50, 0)
    """

    def __init__(
        self,
        engine: AsyncEngine,
        job_status: ReadJobStatus,
        lines_reader: JobLinesReader,
        codings_reader: CodingsReader,
    ) -> None:
        self._engine = engine
        self._job_status = job_status
        self._lines_reader = lines_reader
        self._codings_reader = codings_reader

    async def execute(self, job_id: str, limit: int, offset: int) -> list[ResultLine]:
        """Return the page. Lines not coded yet, or not coded at all, carry no coding.

        Example:
            await list_results.execute("3f2a...", limit=50, offset=0)

        Raises:
            JobNotFoundError: when no job has this identifier.
        """
        await self._job_status.execute(job_id)
        async with self._engine.connect() as connection:
            lines = await self._lines_reader.read_job_lines(connection, job_id, limit, offset)
            codings = await self._codings_reader.read_codings(
                connection, [line.line_id for line in lines]
            )
        return [
            ResultLine(
                invoice_number=line.invoice_number,
                line_position=line.position,
                line_description=line.description,
                target_sheet=coding.target_sheet if coding else None,
                item_number=coding.item_number if coding else None,
                catalog_description=coding.catalog_description if coding else None,
            )
            for line in lines
            for coding in [codings.get(line.line_id)]
        ]
