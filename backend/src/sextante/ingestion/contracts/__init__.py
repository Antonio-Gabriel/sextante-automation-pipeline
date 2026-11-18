"""Published contract of the ingestion module: what other modules may import (02 §2.1)."""

from sextante.ingestion.application.ports import JobLinesReader
from sextante.ingestion.application.read_job_status import JobNotFoundError, ReadJobStatus
from sextante.ingestion.application.records import JobLine
from sextante.ingestion.domain.model import (
    BilledEntityBlock,
    ExtractedInvoice,
    ExtractedLine,
    ExtractionRejection,
    FileFormat,
    PartyIdentity,
    RejectionReason,
    StoredInvoice,
    StoredLine,
    SummaryRow,
)
from sextante.ingestion.domain.ports import InvoiceExtractor

__all__ = [
    "BilledEntityBlock",
    "ExtractedInvoice",
    "ExtractedLine",
    "ExtractionRejection",
    "FileFormat",
    "InvoiceExtractor",
    "JobLine",
    "JobLinesReader",
    "JobNotFoundError",
    "PartyIdentity",
    "ReadJobStatus",
    "RejectionReason",
    "StoredInvoice",
    "StoredLine",
    "SummaryRow",
]
