"""Closed sets of job and invoice states."""

from enum import StrEnum
from typing import Final


class JobStatus(StrEnum):
    """Life of an upload job (D-3.4)."""

    QUEUED = "queued"
    RUNNING = "running"
    # Claimed, with invoices waiting for room under the model call ceiling (SEC-12).
    WAITING_MODEL = "waiting_model"
    COMPLETED = "completed"
    FAILED = "failed"


# A job a worker holds: running, or waiting for the model call ceiling.
CLAIMED_JOB_STATUSES: Final = frozenset({JobStatus.RUNNING, JobStatus.WAITING_MODEL})


class InvoiceStatus(StrEnum):
    """Life of one invoice inside a job."""

    QUEUED = "queued"
    ENCODED = "encoded"
    NOT_CODED = "not_coded"
    REJECTED = "rejected"
    FAILED = "failed"
