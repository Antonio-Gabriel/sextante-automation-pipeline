"""Job progress: invoices by status and the tokens spent (REQ-PLT-001, REQ-AUD-004).

A read model composing published readers, so no module reads another's tables.
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine

from sextante.ingestion.contracts import ReadJobStatus
from sextante.matching.contracts import TokenUsageReader


@dataclass(frozen=True, slots=True)
class JobProgress:
    """Status, invoice counts by status and in total, and token usage of a job."""

    job_id: str
    status: str
    invoice_counts: dict[str, int]
    invoice_total: int
    input_tokens: int
    output_tokens: int
    # Tokens of each invoice that had a model call, by invoice identifier (REQ-AUD-004).
    invoice_tokens: dict[str, tuple[int, int]]


class ReadJobProgress:
    """Return a job's progress.

    Example:
        progress = await ReadJobProgress(engine, status, usage).execute(job_id)
    """

    def __init__(
        self, engine: AsyncEngine, job_status: ReadJobStatus, usage_reader: TokenUsageReader
    ) -> None:
        self._engine = engine
        self._job_status = job_status
        self._usage_reader = usage_reader

    async def execute(self, job_id: str) -> JobProgress:
        """Return the progress.

        Example:
            (await read_progress.execute("3f2a...")).invoice_total  # 2

        Raises:
            JobNotFoundError: when no job has this identifier.
        """
        summary = await self._job_status.execute(job_id)
        async with self._engine.connect() as connection:
            usage = await self._usage_reader.read_token_usage(connection, summary.invoice_ids)
        return JobProgress(
            job_id=summary.job_id,
            status=summary.status,
            invoice_counts=summary.invoice_counts,
            invoice_total=len(summary.invoice_ids),
            input_tokens=sum(tokens[0] for tokens in usage.values()),
            output_tokens=sum(tokens[1] for tokens in usage.values()),
            invoice_tokens=usage,
        )
