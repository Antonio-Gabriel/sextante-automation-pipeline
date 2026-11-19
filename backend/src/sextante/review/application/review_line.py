"""Accept or correct a coded line (REQ-REV-002 to REQ-REV-005, REQ-REV-007).

Both run inside the caller's transaction, the one that also records the idempotency
key (SEC-19), so the review, its audit event and the key are stored together or not at all.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.catalog.contracts import Catalog, CatalogItem, ItemNumber, TargetSheet
from sextante.ingestion.contracts import JobLinesReader
from sextante.matching.contracts import CodingsReader, LineCoding
from sextante.platform.audit import AuditEventRepository
from sextante.platform.clock import Clock, IdentifierGenerator
from sextante.platform.errors import DomainError
from sextante.review.application.codings_in_force import CodingInForce, in_force
from sextante.review.application.ports import ReviewRepositoryPort
from sextante.review.domain.review_state import (
    ItemNotInSheetError,
    LineReview,
    LineWithoutSheetError,
    ReviewNotPendingError,
    ReviewStatus,
)


class EncodedLineNotFoundError(DomainError):
    """No coded line has this identifier."""

    user_message_key = "errors.review.line_not_found"


@dataclass(frozen=True, slots=True)
class ReviewCollaborators:
    """Everything ReviewLine needs, injected (04-padroes-de-codigo.md §4)."""

    codings: CodingsReader
    lines: JobLinesReader
    reviews: ReviewRepositoryPort
    catalog: Catalog
    audit: AuditEventRepository
    clock: Clock
    identifiers: IdentifierGenerator
    reviewer_id: str


class ReviewLine:
    """The reviewer's two actions on a coded line.

    Example:
        review = await ReviewLine(collaborators).correct(connection, line_id, "O00051", None)
    """

    def __init__(self, collaborators: ReviewCollaborators) -> None:
        self._deps = collaborators

    async def accept(
        self, connection: AsyncConnection, encoded_line_id: str, note: str | None
    ) -> CodingInForce:
        """Move a pending line to accepted, keeping its code.

        Example:
            await review_line.accept(connection, "3f2a...", "Confirmado com o fornecedor.")

        Raises:
            EncodedLineNotFoundError: when no coded line has this identifier.
            LineWithoutSheetError: when the line has no target sheet.
            ReviewNotPendingError: when the line is not pending.
        """
        coding, current, _ = await self._current(connection, encoded_line_id)
        if current.review_status != ReviewStatus.PENDING:
            raise ReviewNotPendingError(
                f"Line {encoded_line_id!r} is {current.review_status}. Expected a pending line."
            )
        review = LineReview(
            encoded_line_id,
            ReviewStatus.ACCEPTED,
            current.item_number,
            current.catalog_description,
            _note_in_force(note, current),
        )
        await self._record(connection, current, review, "line_accepted")
        return in_force(coding, review)

    async def correct(
        self, connection: AsyncConnection, encoded_line_id: str, item_number: str, note: str | None
    ) -> CodingInForce:
        """Assign another item of the line's target sheet; the line becomes corrected.

        Example:
            await review_line.correct(connection, "3f2a...", "O00051", "Correio, não outras.")

        Raises:
            EncodedLineNotFoundError: when no coded line has this identifier.
            LineWithoutSheetError: when the line has no target sheet.
            ItemNotInSheetError: when the item is malformed or not in the line's sheet.
        """
        coding, current, sheet = await self._current(connection, encoded_line_id)
        catalog_item = self._item_of_sheet(item_number, sheet)
        review = LineReview(
            encoded_line_id,
            ReviewStatus.CORRECTED,
            catalog_item.item_number.value,
            catalog_item.description_pt,
            _note_in_force(note, current),
        )
        await self._record(connection, current, review, "line_corrected")
        return in_force(coding, review)

    async def _current(
        self, connection: AsyncConnection, encoded_line_id: str
    ) -> tuple[LineCoding, CodingInForce, TargetSheet]:
        coding = await self._deps.codings.read_encoded_line(connection, encoded_line_id)
        # A line of a deleted job is hidden like the job: it is not reviewed either.
        if coding is None or not await self._deps.lines.line_in_active_job(
            connection, coding.invoice_line_id
        ):
            raise EncodedLineNotFoundError(f"Coded line {encoded_line_id!r} does not exist.")
        # A line of an ambiguous invoice has no sheet: it is unblocked by resolving the
        # entity of its invoice (REQ-REV-006), never line by line (REQ-REV-002).
        if coding.target_sheet is None:
            raise LineWithoutSheetError(
                f"Coded line {encoded_line_id!r} has no target sheet. Expected the entity "
                "of its invoice to be resolved first."
            )
        reviews = await self._deps.reviews.read_reviews(connection, [encoded_line_id])
        sheet = TargetSheet(coding.target_sheet)
        return coding, in_force(coding, reviews.get(encoded_line_id)), sheet

    def _item_of_sheet(self, item_number: str, sheet: TargetSheet) -> CatalogItem:
        # Validated on the server against the line's own sheet: the review cannot route
        # around the sheet that step 2 decided (REQ-REV-002).
        try:
            number = ItemNumber(item_number)
        except ValueError:
            raise ItemNotInSheetError(
                f"Item number {item_number!r} is malformed. Expected a value of column No., "
                "for example 'O00051'."
            ) from None
        found = next(
            (c for c in self._deps.catalog.items_of(sheet) if c.item_number == number), None
        )
        if found is None:
            raise ItemNotInSheetError(
                f"Item {number} is not in sheet {sheet.value}. Expected an item of that sheet."
            )
        return found

    async def _record(
        self,
        connection: AsyncConnection,
        previous: CodingInForce,
        review: LineReview,
        event_type: str,
    ) -> None:
        deps = self._deps
        now = deps.clock.now()
        await deps.reviews.save_review(connection, review, deps.reviewer_id, now)
        await deps.audit.append(
            connection,
            deps.identifiers.new_id(),
            event_type,
            ("encoded_line", review.encoded_line_id),
            _audit_payload(previous, review),
            now,
            author=deps.reviewer_id,
        )


def _note_in_force(note: str | None, current: CodingInForce) -> str | None:
    # A review without a note keeps the note already in force.
    return note if note is not None else current.review_note


def _audit_payload(previous: CodingInForce, review: LineReview) -> Mapping[str, object]:
    # The previous and the new value of everything the review can change (REQ-REV-004).
    return {
        "previous_item_number": previous.item_number,
        "new_item_number": review.item_number,
        "previous_review_status": previous.review_status,
        "new_review_status": review.review_status.value,
        "previous_note": previous.review_note,
        "new_note": review.note,
    }
