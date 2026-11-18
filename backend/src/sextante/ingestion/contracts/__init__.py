"""Published contract of the ingestion module: what other modules may import (02 §2.1).

The tables are published read-only, for read models that join invoices with their coding.
"""

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
from sextante.ingestion.infrastructure.tables import (
    INVOICE_HEADER_TABLE,
    INVOICE_LINE_TABLE,
    INVOICE_TABLE,
)

__all__ = [
    "INVOICE_HEADER_TABLE",
    "INVOICE_LINE_TABLE",
    "INVOICE_TABLE",
    "BilledEntityBlock",
    "ExtractedInvoice",
    "ExtractedLine",
    "ExtractionRejection",
    "FileFormat",
    "InvoiceExtractor",
    "PartyIdentity",
    "RejectionReason",
    "StoredInvoice",
    "StoredLine",
    "SummaryRow",
]
