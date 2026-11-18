"""PDF extraction in a separate process, with a memory and a time limit (SEC-16).

A PDF is input from outside. One built to expand on decompression, or to take long to
read, would otherwise exhaust the server's memory or hold the worker. Read in a child
process, it can only exhaust the child: over a limit the child is stopped and the
document is refused as unsupported, with the limit in the log and never its content.

The memory limit is the child's address space (``RLIMIT_AS``), which Linux enforces;
where the platform does not, only the time limit applies, and the child says so in the
log. Children start from a server process with the extractor already imported, so each
PDF does not pay for a fresh interpreter.
"""

import logging
import multiprocessing
from dataclasses import dataclass
from multiprocessing.connection import Connection
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
_CONTEXT: Final = multiprocessing.get_context("forkserver")
_CONTEXT.set_forkserver_preload([__name__])

Extraction = ExtractedInvoice | ExtractionRejection


@dataclass(frozen=True, slots=True)
class ExtractionLimits:
    """What reading one PDF may use: address space in bytes and wall time in seconds."""

    memory_bytes: int
    timeout_seconds: float


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
        outcome = self._run_child(content)
        if isinstance(outcome, str):
            return self._refuse_over(outcome)
        return outcome

    def _run_child(self, content: bytes) -> Extraction | str:
        receiver, sender = _CONTEXT.Pipe(duplex=False)
        arguments = (content, self._min_chars_per_page, self._limits.memory_bytes)
        child = _CONTEXT.Process(
            target=_extract_in_child, args=(*arguments, correlation_id_var.get(), sender)
        )
        child.start()
        sender.close()
        try:
            return _child_answer(receiver, self._limits.timeout_seconds)
        finally:
            child.kill()
            child.join()
            child.close()
            receiver.close()

    def _refuse_over(self, limit: str) -> ExtractionRejection:
        # The limit and its values only: never a byte of the file (SEC-15).
        logger.warning(
            "pdf_extraction_limit_reached",
            extra={
                "limit": limit,
                "memory_mib": self._limits.memory_bytes // MIB,
                "timeout_seconds": self._limits.timeout_seconds,
            },
        )
        return ExtractionRejection(RejectionReason.UNSUPPORTED_DOCUMENT_TYPE)


def _child_answer(receiver: Connection, timeout_seconds: float) -> Extraction | str:
    # "time" when no answer came in time; "memory" when the child said so, or died
    # without a word, which is how the kernel ends a process out of memory.
    if not receiver.poll(timeout_seconds):
        return "time"
    try:
        kind, value = receiver.recv()
    except EOFError:
        return "memory"
    if kind == "error":
        raise PdfExtractionError(f"PDF extraction failed in the child with {value}.")
    answer: Extraction | str = value
    return answer


def _extract_in_child(
    content: bytes,
    min_chars_per_page: int,
    memory_bytes: int,
    correlation_id: str,
    sender: Connection,
) -> None:
    # Runs in the child: its own logging, the job's correlation id, then the limit.
    configure_logging()
    correlation_id_var.set(correlation_id)
    _limit_memory(memory_bytes)
    try:
        sender.send(
            ("result", PdfInvoiceExtractor(min_chars_per_page).extract(content, FileFormat.PDF))
        )
    except MemoryError:
        sender.send(("limit", "memory"))
    except Exception as error:
        # Reported to the parent by type, which fails the invoice: never swallowed.
        sender.send(("error", type(error).__name__))
    finally:
        sender.close()


def _limit_memory(memory_bytes: int) -> None:
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
    except (ImportError, ValueError, OSError) as error:
        logger.warning("pdf_memory_limit_unavailable", extra={"error_type": type(error).__name__})
