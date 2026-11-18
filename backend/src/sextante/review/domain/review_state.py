"""Review state of a coded line and its refusals (REQ-REV-002, REQ-REV-005, REQ-REV-007)."""

from dataclasses import dataclass
from enum import StrEnum

from sextante.platform.errors import DomainError


class ReviewStatus(StrEnum):
    """The closed set of review states (REQ-REV-005)."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    CORRECTED = "corrected"


class LineWithoutSheetError(DomainError):
    """A line without target sheet is unblocked by resolving its entity, not per line (L-13)."""

    user_message_key = "errors.review.line_without_sheet"


class ItemNotInSheetError(DomainError):
    """The chosen item is not in the line's target sheet (REQ-REV-002)."""

    user_message_key = "errors.review.item_not_in_sheet"


class ReviewNotPendingError(DomainError):
    """Only a pending line is accepted (REQ-REV-007)."""

    user_message_key = "errors.review.not_pending"


@dataclass(frozen=True, slots=True)
class LineReview:
    """The values in force of a reviewed line, kept apart from its coding (REQ-REV-004)."""

    encoded_line_id: str
    review_status: ReviewStatus
    item_number: str | None
    catalog_description: str | None
    note: str | None
