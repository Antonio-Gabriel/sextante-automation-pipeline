"""Closed sets of job and invoice states."""

from enum import StrEnum


class JobStatus(StrEnum):
    """Life of an upload job (D-3.4)."""

    QUEUED = "queued"
    RUNNING = "running"
    # Claimed, with invoices waiting for room under the model call ceiling (SEC-12).
    WAITING_MODEL = "waiting_model"
    COMPLETED = "completed"
    FAILED = "failed"


class InvoiceStatus(StrEnum):
    """Life of one invoice inside a job."""

    QUEUED = "queued"
    ENCODED = "encoded"
    NOT_CODED = "not_coded"
    REJECTED = "rejected"
    FAILED = "failed"
