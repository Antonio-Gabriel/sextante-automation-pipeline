"""Records exchanged between ingestion use cases and their repository port."""

from dataclasses import dataclass


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
