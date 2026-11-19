"""List jobs, delete one softly, and restore deleted ones (frontend ticket 07).

A deleted job is hidden from every read; its invoices, codings, reviews and audit stay.
Uploading again a file of a deleted job restores the job: one invoice per content
(REQ-ING-007), so nothing is coded twice and no review is lost.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from sextante.ingestion.application.ports import JobRecordsPort
from sextante.ingestion.application.read_job_status import JobNotFoundError
from sextante.ingestion.application.records import JobListEntry
from sextante.ingestion.domain.statuses import JobStatus
from sextante.platform.audit import AuditEventRepository
from sextante.platform.clock import Clock, IdentifierGenerator
from sextante.platform.errors import DomainError

# A queued or running job is still being coded: deleting it would hide work in progress.
DELETABLE_STATUSES: Final = frozenset({JobStatus.COMPLETED, JobStatus.FAILED})


class JobNotDeletableError(DomainError):
    """Only a finished job, completed or failed, is deleted."""

    user_message_key = "errors.job.not_deletable"


@dataclass(frozen=True, slots=True)
class JobCollaborators:
    """Everything the job use cases need, injected (04-padroes-de-codigo.md §4)."""

    engine: AsyncEngine
    repository: JobRecordsPort
    audit: AuditEventRepository
    clock: Clock
    identifiers: IdentifierGenerator
    reviewer_id: str


class ListJobs:
    """Return one page of the jobs not deleted, newest first.

    Example:
        jobs = await ListJobs(collaborators).execute(50, 0)
    """

    def __init__(self, collaborators: JobCollaborators) -> None:
        self._deps = collaborators

    async def execute(self, limit: int, offset: int) -> list[JobListEntry]:
        """Return the page."""
        async with self._deps.engine.connect() as connection:
            return await self._deps.repository.list_jobs(connection, limit, offset)


class DeleteJob:
    """Hide a finished job. Deleting it again changes nothing.

    Example:
        await DeleteJob(collaborators).execute(connection, "3f2a...")
    """

    def __init__(self, collaborators: JobCollaborators) -> None:
        self._deps = collaborators

    async def execute(self, connection: AsyncConnection, job_id: str) -> None:
        """Delete the job, softly, in the caller's transaction (SEC-19).

        Raises:
            JobNotFoundError: when no job has this identifier.
            JobNotDeletableError: when the job is queued or running.
        """
        deps = self._deps
        state = await deps.repository.job_removal_state(connection, job_id)
        if state is None:
            raise JobNotFoundError(f"Job {job_id!r} does not exist.")
        if state.deleted:
            return
        if JobStatus(state.status) not in DELETABLE_STATUSES:
            raise JobNotDeletableError(
                f"Job {job_id!r} is {state.status}. Expected a completed or failed job."
            )
        now = deps.clock.now()
        await deps.repository.mark_job_deleted(connection, job_id, now)
        await _audit(deps, connection, "job_deleted", job_id)


class RestoreJobs:
    """Show again the deleted jobs among these, as an upload of their files does.

    Example:
        restored = await RestoreJobs(collaborators).execute(["3f2a..."])
    """

    def __init__(self, collaborators: JobCollaborators) -> None:
        self._deps = collaborators

    async def execute(self, job_ids: Sequence[str]) -> tuple[str, ...]:
        """Restore the deleted ones and return them; the others are left as they are."""
        if not job_ids:
            return ()
        restored: list[str] = []
        async with self._deps.engine.begin() as connection:
            for job_id in job_ids:
                if await self._deps.repository.restore_job(connection, job_id):
                    await _audit(self._deps, connection, "job_restored", job_id)
                    restored.append(job_id)
        return tuple(restored)


async def _audit(
    deps: JobCollaborators, connection: AsyncConnection, event: str, job_id: str
) -> None:
    await deps.audit.append(
        connection,
        deps.identifiers.new_id(),
        event,
        ("job", job_id),
        {},
        deps.clock.now(),
        author=deps.reviewer_id,
    )
