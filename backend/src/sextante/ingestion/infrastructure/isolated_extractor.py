"""PDF extraction in a separate process, with a memory and a time limit (SEC-16).

A PDF is input from outside. One built to expand on decompression, or to take long to
read, would otherwise exhaust the server's memory or hold the worker. Read in a child
process, it can only exhaust the child: over a limit the child is stopped and the
document is refused as unsupported, with the limit in the log and never its content.

The memory limit is the child's address space (``RLIMIT_AS``), which only Linux
enforces: on Linux a limit that cannot be set fails the invoice, never reads without
it; elsewhere the child says in the log that only the time limit applies. The child
also gets a CPU time limit, so it ends by itself if the server dies while it reads.
Children start from a server process with the extractor already imported where the
platform has one, so each PDF does not pay for a fresh interpreter.
"""

import functools
import logging
import multiprocessing
import signal
import sys
from dataclasses import dataclass
from enum import StrEnum
from multiprocessing.connection import Connection
from multiprocessing.context import ForkServerContext, SpawnContext
from multiprocessing.process import BaseProcess
from typing import Final

from sextante.ingestion.domain.model import (
    ExtractedInvoice,
    ExtractionRejection,
    FileFormat,
    RejectionReason,
)
from sextante.ingestion.infrastructure.pdf_invoice_extractor import PdfInvoiceExtractor
from sextante.platform.structured_logging import configure_logging, correlation_id_var

logger = logging.getLogger(__name__)

MIB: Final = 1024 * 1024
# CPU seconds the child may use beyond the wall time limit, before the kernel ends it.
CPU_GRACE_SECONDS: Final = 5

Extraction = ExtractedInvoice | ExtractionRejection


class ExtractionLimit(StrEnum):
    """The limit a PDF reached, as the log names it."""

    MEMORY = "memory"
    TIME = "time"


class _Message(StrEnum):
    # What the child sends the parent: one message, then it ends.
    RESULT = "result"
    LIMIT = "limit"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ExtractionLimits:
    """What reading one PDF may use: address space in bytes and wall time in seconds."""

    memory_bytes: int
    timeout_seconds: float


@dataclass(frozen=True, slots=True)
class _ChildJob:
    # Everything that crosses into the child process.
    content: bytes
    min_chars_per_page: int
    limits: ExtractionLimits
    correlation_id: str


class PdfExtractionError(RuntimeError):
    """The child failed for a reason other than a limit; the invoice fails, as before."""


class IsolatedPdfExtractor:
    """InvoiceExtractor that reads each PDF in a child process, within limits.

    Example:
        extractor = IsolatedPdfExtractor(100, ExtractionLimits(512 * MIB, 30.0))
        extractor.extract(pdf_bytes, FileFormat.PDF)
    """

    def __init__(self, min_chars_per_page: int, limits: ExtractionLimits) -> None:
        self._min_chars_per_page = min_chars_per_page
        self._limits = limits

    def extract(self, content: bytes, file_format: FileFormat) -> Extraction:
        """Extract in a child process; over a limit, refuse as unsupported.

        Example:
            extractor.extract(pdf_bytes, FileFormat.PDF)

        Raises:
            PdfExtractionError: when the child fails for another reason.
        """
        if file_format is not FileFormat.PDF:
            return ExtractionRejection(RejectionReason.UNSUPPORTED_DOCUMENT_TYPE)
        job = _ChildJob(content, self._min_chars_per_page, self._limits, correlation_id_var.get())
        outcome = _run_child(job)
        if isinstance(outcome, ExtractionLimit):
            return self._refuse_over(outcome)
        return outcome

    def _refuse_over(self, limit: ExtractionLimit) -> ExtractionRejection:
        # The limit and its values only: never a byte of the file (SEC-15).
        logger.warning(
            "pdf_extraction_limit_reached",
            extra={
                "limit": limit.value,
                "memory_mib": self._limits.memory_bytes // MIB,
                "timeout_seconds": self._limits.timeout_seconds,
            },
        )
        return ExtractionRejection(RejectionReason.UNSUPPORTED_DOCUMENT_TYPE)


def _run_child(job: _ChildJob) -> Extraction | ExtractionLimit:
    context = _process_context()
    receiver, sender = context.Pipe(duplex=False)
    child = context.Process(target=_extract_in_child, args=(job, sender))
    child.start()
    sender.close()
    try:
        if not receiver.poll(job.limits.timeout_seconds):
            return ExtractionLimit.TIME
        return _child_answer(receiver, child)
    finally:
        child.kill()
        child.join()
        child.close()
        receiver.close()


def _child_answer(receiver: Connection, child: BaseProcess) -> Extraction | ExtractionLimit:
    try:
        kind, payload = receiver.recv()
    except EOFError:
        return _silent_death(child)
    if kind == _Message.RESULT:
        extraction: Extraction = payload
        return extraction
    if kind == _Message.LIMIT:
        return ExtractionLimit(payload)
    logger.error("pdf_extraction_failed", extra={"error_type": payload})
    raise PdfExtractionError(
        f"PDF extraction failed in the child with {payload}. "
        "Expected an extraction, a refusal or a limit reached."
    )


def _silent_death(child: BaseProcess) -> ExtractionLimit:
    # The kernel ends a process out of memory with SIGKILL: that is the memory limit.
    # Any other death is a failure, never passed off as a limit.
    child.join()
    if child.exitcode == -signal.SIGKILL:
        return ExtractionLimit.MEMORY
    raise PdfExtractionError(
        f"PDF extraction child ended with exit code {child.exitcode} and no answer. "
        "Expected one answer before it ends."
    )


def _extract_in_child(job: _ChildJob, sender: Connection) -> None:
    # Runs in the child: its own logging, the job's correlation id, then the limits.
    configure_logging()
    correlation_id_var.set(job.correlation_id)
    try:
        _limit_child(job.limits)
        extraction = PdfInvoiceExtractor(job.min_chars_per_page).extract(
            job.content, FileFormat.PDF
        )
        sender.send((_Message.RESULT, extraction))
    except MemoryError:
        sender.send((_Message.LIMIT, ExtractionLimit.MEMORY.value))
    except Exception as error:
        # Reported to the parent by type, which fails the invoice: never swallowed.
        sender.send((_Message.ERROR, type(error).__name__))
    finally:
        sender.close()


def _limit_child(limits: ExtractionLimits) -> None:
    # On Linux both limits are set or the read does not happen (fails closed). Elsewhere
    # the memory limit is not enforced, and the log says so.
    if sys.platform != "linux":
        logger.warning("pdf_memory_limit_unavailable", extra={"platform": sys.platform})
        return
    import resource

    cpu_seconds = int(limits.timeout_seconds) + CPU_GRACE_SECONDS
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
    resource.setrlimit(resource.RLIMIT_AS, (limits.memory_bytes, limits.memory_bytes))


@functools.cache
def _process_context() -> ForkServerContext | SpawnContext:
    # A forkserver where the platform has one: never fork a process that runs threads,
    # nor start a fresh interpreter per PDF. Built on first use, not at import.
    if "forkserver" not in multiprocessing.get_all_start_methods():
        return multiprocessing.get_context("spawn")
    context = multiprocessing.get_context("forkserver")
    context.set_forkserver_preload([__name__])
    return context
