"""Extracted invoice: what the InvoiceExtractor port returns (D-3.6, REQ-ING-003/004)."""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from sextante.ingestion.domain.line_type import LineType


class FileFormat(StrEnum):
    """Accepted upload formats, decided by real content, never by extension (REQ-ING-001)."""

    PDF = "pdf"
    XLSX = "xlsx"


class RejectionReason(StrEnum):
    """Why an uploaded document was refused and not coded (REQ-ING-002, REQ-ING-009)."""

    PDF_WITHOUT_TEXT_LAYER = "pdf_without_text_layer"
    UNSUPPORTED_DOCUMENT_TYPE = "unsupported_document_type"
    # No extractor reads this format in this version, such as XLSX (D-3.6).
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
    line_type: LineType


@dataclass(frozen=True, slots=True)
class StoredInvoice:
    """A persisted, normalized extraction, as handed to coding."""

    invoice_id: str
    supplier_name: str | None
    currency: str | None
    billed_entities: tuple[BilledEntityBlock, ...]
    lines: tuple[StoredLine, ...]


def missing_fields(invoice: ExtractedInvoice) -> tuple[str, ...]:
    """Names of the fields the extraction did not find: recorded as missing, never inferred.

    Names only, never the text around them, so the result may go to logs and the audit
    trail (REQ-ING-003, SEC-15).

    Example:
        missing_fields(extraction)  # ("invoice_date", "line_1.vat_rate")
    """
    header = {
        "supplier_name": invoice.supplier.name,
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date,
        "currency": invoice.currency,
        "billed_entity": invoice.billed_entities or None,
    }
    names = [name for name, value in header.items() if value is None]
    names += [
        f"line_{line.position}.{name}"
        for line in invoice.lines
        for name in ("quantity", "unit_price", "vat_rate", "amount")
        if getattr(line, name) is None
    ]
    return tuple(names)
