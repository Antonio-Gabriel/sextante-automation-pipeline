"""Accept uploaded invoice files into a queued job (REQ-PLT-001, REQ-ING-001, REQ-ING-007)."""

import hashlib
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from sextante.ingestion.application.manage_jobs import RestoreJobs
from sextante.ingestion.application.ports import IngestionRepositoryPort
from sextante.ingestion.application.records import DuplicateContentError, NewInvoice
from sextante.ingestion.domain.file_type import detect_file_format
from sextante.ingestion.domain.ports import InvoiceFileStore
from sextante.ingestion.domain.statuses import JobStatus
from sextante.platform.clock import Clock, IdentifierGenerator
from sextante.platform.errors import DomainError
from sextante.platform.limits import MAX_FILE_NAME_LENGTH, MAX_FILES_PER_UPLOAD


class UploadRejectedError(DomainError):
    """An upload broke a rule of SEC-16. Each subclass names the rule."""


class NoFilesUploadedError(UploadRejectedError):
    """The upload request held no file."""

    user_message_key = "errors.upload.no_files"


class TooManyFilesError(UploadRejectedError):
    """The upload request held more files than MAX_FILES_PER_UPLOAD."""

    user_message_key = "errors.upload.too_many_files"


class UnsupportedFileTypeError(UploadRejectedError):
    """The content is neither PDF nor XLSX by its first bytes (REQ-ING-001)."""

    user_message_key = "errors.upload.unsupported_type"


class InvalidFileNameError(UploadRejectedError):
    """The client's file name is empty, too long or holds control characters."""

    user_message_key = "errors.upload.invalid_file_name"


class FileTooLargeError(UploadRejectedError):
    """One file is larger than MAX_UPLOAD_BYTES."""

    user_message_key = "errors.upload.too_large"


@dataclass(frozen=True, slots=True)
class IncomingFile:
    """One file as received: the name shown by the client, and the content."""

    display_name: str
    content: bytes


@dataclass(frozen=True, slots=True)
class UploadReceipt:
    """The job holding the upload, the earlier jobs of files uploaded before, and those of
    them that were deleted and are now restored."""

    job_id: str
    status: JobStatus
    invoice_count: int
    existing_job_ids: tuple[str, ...]
    restored_job_ids: tuple[str, ...] = ()


def check_file_count(file_count: int) -> None:
    """Refuse an upload with no file, or with more than MAX_FILES_PER_UPLOAD (§9.1).

    Called before any content is read, so the count bounds the memory an upload uses.

    Example:
        check_file_count(len(files))
    """
    if file_count == 0:
        raise NoFilesUploadedError("Upload holds no file. Expected one or more files.")
    if file_count > MAX_FILES_PER_UPLOAD:
        raise TooManyFilesError(
            f"Upload holds {file_count} files. Expected at most {MAX_FILES_PER_UPLOAD}."
        )


class UploadInvoices:
    """Validate files, store them under server names, and queue a job for the new ones.

    Example:
        upload = UploadInvoices(engine, repository, store, (clock, ids), restore)
        receipt = await upload.execute(files, cid)
    """

    def __init__(
        self,
        engine: AsyncEngine,
        repository: IngestionRepositoryPort,
        store: InvoiceFileStore,
        time_and_ids: tuple[Clock, IdentifierGenerator],
        restore: RestoreJobs,
    ) -> None:
        self._engine = engine
        self._repository = repository
        self._store = store
        self._clock, self._identifiers = time_and_ids
        self._restore = restore

    async def execute(self, files: Sequence[IncomingFile], correlation_id: str) -> UploadReceipt:
        """Queue the new files. A file uploaded before is answered with its job (REQ-ING-007).

        Example:
            receipt = await upload.execute([IncomingFile("a.pdf", content)], "3f2a...")

        Raises:
            UploadRejectedError: when a file breaks a rule of SEC-16.
        """
        check_file_count(len(files))
        accepted = [_accept(incoming) for incoming in files]
        for new_file in accepted:
            self._store.save(new_file.storage_name, new_file.content)
        try:
            new_job_id, existing = await self._record(accepted, correlation_id)
        except DuplicateContentError:
            # A concurrent upload of the same content won the unique digest constraint.
            # Recording again now finds that invoice and answers with its job.
            new_job_id, existing = await self._record(accepted, correlation_id)
        # A file of a deleted job brings that job back: its invoice is the one of record.
        restored = await self._restore.execute(existing)
        if new_job_id is None:
            return await self._existing_receipt(existing, len(accepted), restored)
        return UploadReceipt(new_job_id, JobStatus.QUEUED, len(accepted), existing, restored)

    async def _record(
        self, accepted: list["_AcceptedFile"], correlation_id: str
    ) -> tuple[str | None, tuple[str, ...]]:
        # The new job, None when every file was uploaded before, and the earlier jobs.
        job_id = self._identifiers.new_id()
        async with self._engine.connect() as connection, connection.begin() as transaction:
            # The job row is written first: in SQLite this takes the write lock, so the
            # digest lookups below cannot race another upload (D-3.5).
            await self._repository.insert_job(connection, job_id, correlation_id, self._clock.now())
            existing = [await self._insert_or_find(connection, job_id, f) for f in accepted]
            existing_job_ids = tuple(dict.fromkeys(e for e in existing if e is not None))
            if None not in existing:
                await transaction.rollback()
                return None, existing_job_ids
        return job_id, existing_job_ids

    async def _existing_receipt(
        self, existing_job_ids: tuple[str, ...], file_count: int, restored: tuple[str, ...]
    ) -> UploadReceipt:
        # Every file was uploaded before: answer with the existing job and its current
        # state, not an error (D-3.10, REQ-ING-007).
        async with self._engine.connect() as connection:
            summary = await self._repository.job_summary(connection, existing_job_ids[0])
        if summary is None:
            raise LookupError(f"Job {existing_job_ids[0]} of a recorded invoice does not exist.")
        return UploadReceipt(
            existing_job_ids[0], JobStatus(summary.status), file_count, existing_job_ids, restored
        )

    async def _insert_or_find(
        self, connection: AsyncConnection, job_id: str, accepted: "_AcceptedFile"
    ) -> str | None:
        existing_job = await self._repository.find_job_of_digest(connection, accepted.digest)
        if existing_job is not None:
            return existing_job
        new_invoice = NewInvoice(
            invoice_id=self._identifiers.new_id(),
            job_id=job_id,
            content_digest=accepted.digest,
            display_name=accepted.display_name,
            storage_name=accepted.storage_name,
            file_format=accepted.file_format,
        )
        await self._repository.insert_invoice(connection, new_invoice, self._clock.now())
        return None


@dataclass(frozen=True, slots=True)
class _AcceptedFile:
    display_name: str
    content: bytes
    digest: str
    file_format: str

    @property
    def storage_name(self) -> str:
        # Derived from the digest only: the client's name never reaches a path (SEC-16).
        return f"{self.digest}.{self.file_format}"


def _accept(incoming: IncomingFile) -> _AcceptedFile:
    _check_display_name(incoming.display_name)
    file_format = detect_file_format(incoming.content[:8])
    if file_format is None:
        raise UnsupportedFileTypeError(
            "Uploaded content is neither PDF nor XLSX by its first bytes. "
            "Expected a PDF or an XLSX file."
        )
    digest = hashlib.sha256(incoming.content).hexdigest()
    return _AcceptedFile(incoming.display_name, incoming.content, digest, file_format.value)


def _check_display_name(display_name: str) -> None:
    has_control = any(unicodedata.category(character) in {"Cc", "Cf"} for character in display_name)
    if not display_name or len(display_name) > MAX_FILE_NAME_LENGTH or has_control:
        raise InvalidFileNameError(
            f"File name of {len(display_name)} characters is empty, too long or holds control "
            f"characters. Expected 1 to {MAX_FILE_NAME_LENGTH} printable characters."
        )
