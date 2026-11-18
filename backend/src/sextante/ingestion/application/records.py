"""Records exchanged between ingestion use cases and their repository port."""

from dataclasses import dataclass
from datetime import datetime

from sextante.ingestion.domain.statuses import InvoiceStatus


@dataclass(frozen=True, slots=True)
class NewInvoice:
    """An accepted upload, ready to be recorded."""

    invoice_id: str
    job_id: str
    content_digest: str
    display_name: str
    storage_name: str
    file_format: str


@dataclass(frozen=True, slots=True)
class ClaimedJob:
    """A job taken by the worker, with the correlation id of the upload that created it."""

    job_id: str
    correlation_id: str


@dataclass(frozen=True, slots=True)
class QueuedInvoice:
    """An invoice waiting for extraction and coding."""

    invoice_id: str
    storage_name: str
    file_format: str


@dataclass(frozen=True, slots=True)
class JobSummary:
    """Job status and invoice counts by status (REQ-PLT-001)."""

    job_id: str
    status: str
    invoice_counts: dict[str, int]
    invoice_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class JobLine:
    """One invoice line of a job, as read for listings (REQ-REV-001)."""

    line_id: str
    invoice_id: str
    invoice_number: str | None
    position: int
    description: str
    billed_entity: str | None
    entity_verdict: str | None
    entity_reason: str | None = None
    # The invoice uploaded earlier with the same supplier and number (REQ-ING-011).
    possible_duplicate_of: str | None = None


class DuplicateContentError(Exception):
    """Raised by the repository port when the content digest is already recorded.

    The unique constraint on the digest decides concurrent uploads (REQ-ING-007); this
    error carries that decision to the use case without a database type.
    """


@dataclass(frozen=True, slots=True)
class EntityResolutionRecord:
    """A reviewer's decision on an ambiguous entity (REQ-REV-006). Plain text, as above."""

    verdict: str
    note: str
    resolved_by: str
    resolved_at: datetime


@dataclass(frozen=True, slots=True)
class EntityCheckRecord:
    """The entity verdict, its reason and the routing, as stored on the invoice header.

    Plain text here: the closed sets belong to the matching module (D-3.15).
    """

    verdict: str
    reason: str | None
    target_sheet: str | None


@dataclass(frozen=True, slots=True)
class ExportInvoice:
    """One invoice of a job as the export reads it: header, status and lines (REQ-EXP-004)."""

    invoice_id: str
    status: InvoiceStatus
    status_reason: str | None
    content_digest: str
    supplier_name: str | None
    supplier_nif: str | None
    invoice_number: str | None
    billed_entity: str | None
    care_of: tuple[str, ...]
    entity_verdict: str | None
    lines: tuple["ExportLine", ...]
    entity_reason: str | None = None
    earlier_copy: "EarlierCopy | None" = None


@dataclass(frozen=True, slots=True)
class EarlierCopy:
    """The invoice a possible duplicate points at, as a person recognizes it (REQ-ING-011)."""

    file_name: str
    uploaded_at: datetime


@dataclass(frozen=True, slots=True)
class ExportLine:
    """One invoice line, in document order."""

    line_id: str
    position: int
    description: str


@dataclass(frozen=True, slots=True)
class InvoiceState:
    """Where an invoice is: its job, its status, and its entity verdict once checked."""

    job_id: str
    status: InvoiceStatus
    entity_verdict: str | None = None
    entity_reason: str | None = None
