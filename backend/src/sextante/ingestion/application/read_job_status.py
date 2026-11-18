"""Read the status of a job (REQ-PLT-001)."""

from sqlalchemy.ext.asyncio import AsyncEngine

from sextante.ingestion.application.ports import IngestionRepositoryPort
from sextante.ingestion.application.records import JobSummary
from sextante.platform.errors import DomainError


class JobNotFoundError(DomainError):
    """No job has this identifier."""

    user_message_key = "errors.job.not_found"


class ReadJobStatus:
    """Return a job's status and its invoices counted by status.

    Example:
        summary = await ReadJobStatus(engine, repository).execute(job_id)
    """

    def __init__(self, engine: AsyncEngine, repository: IngestionRepositoryPort) -> None:
        self._engine = engine
        self._repository = repository

    async def execute(self, job_id: str) -> JobSummary:
        """Return the job summary.

        Example:
            (await read_status.execute("3f2a...")).invoice_counts  # {"encoded": 1}

        Raises:
            JobNotFoundError: when no job has this identifier.
        """
        async with self._engine.connect() as connection:
            summary = await self._repository.job_summary(connection, job_id)
        if summary is None:
            raise JobNotFoundError(
                f"Job {job_id!r} does not exist. Expected the id returned by an upload."
            )
        return summary
