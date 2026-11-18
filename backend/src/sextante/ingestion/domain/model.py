"""Extracted invoice: what the InvoiceExtractor port returns (D-3.6, REQ-ING-003/004)."""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class FileFormat(StrEnum):
    """Accepted upload formats, decided by real content, never by extension (REQ-ING-001)."""

    PDF = "pdf"
    XLSX = "xlsx"


class RejectionReason(StrEnum):
    """Why an uploaded document was refused and not coded (REQ-ING-002, REQ-ING-009)."""

    PDF_WITHOUT_TEXT_LAYER = "pdf_without_text_layer"
    UNSUPPORTED_DOCUMENT_TYPE = "unsupported_document_type"
    EXTRACTOR_NOT_CONFIGURED = "extractor_not_configured"


@dataclass(frozen=True, slots=True)
class PartyIdentity:
    """A name with its tax number (NIF), either of which may be absent from the document."""

    name: str | None
    nif: str | None


@dataclass(frozen=True, slots=True)
class BilledEntityBlock:
    """The billed-entity block: its first line is the billed entity (REQ-ING-005, D-3.15).

    ``care_of`` holds the "c/o" or "a/c" lines, which never enter the entity check.
    """

    name: str
    nif: str | None
    care_of: tuple[str, ...]
    address_lines: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExtractedLine:
    """One line of the invoice table, in document order (REQ-ING-004)."""

    position: int
    description: str
    quantity: Decimal | None
    unit_price: Decimal | None
    vat_rate: Decimal | None
    amount: Decimal | None


@dataclass(frozen=True, slots=True)
class SummaryRow:
    """A subtotal, tax or total printed under the table. Not an invoice line (D-3.17)."""

    label: str
    amount: Decimal | None


@dataclass(frozen=True, slots=True)
class ExtractedInvoice:
    """Everything read from one invoice. Absent fields stay None, never inferred."""

    supplier: PartyIdentity
    invoice_number: str | None
    invoice_date: str | None
    currency: str | None
    billed_entities: tuple[BilledEntityBlock, ...]
    lines: tuple[ExtractedLine, ...]
    summary_rows: tuple[SummaryRow, ...]
    notes: str


@dataclass(frozen=True, slots=True)
class ExtractionRejection:
    """The extractor refused the document, with a reason from a closed set."""

    reason: RejectionReason


@dataclass(frozen=True, slots=True)
class StoredLine:
    """A persisted invoice line, as handed to coding."""

    line_id: str
    position: int
    description: str


@dataclass(frozen=True, slots=True)
class StoredInvoice:
    """A persisted extraction, as handed to coding."""

    invoice_id: str
    billed_entities: tuple[BilledEntityBlock, ...]
    lines: tuple[StoredLine, ...]
