"""The coding of each line as it stands after review (REQ-REV-004, REQ-EXP-004).

The values in force are the reviewer's when a review exists, the system's otherwise.
Results and export both read through here, so the two never disagree.
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.matching.contracts import CodingsReader, LineCoding
from sextante.review.application.ports import ReviewRepositoryPort
from sextante.review.domain.review_state import LineReview


@dataclass(frozen=True, slots=True)
class CodingInForce:
    """One line's coding with the reviewer's values applied, and the review note."""

    encoded_line_id: str
    target_sheet: str | None
    item_number: str | None
    catalog_description: str | None
    confidence: str
    review_status: str
    flags: tuple[str, ...]
    note: str | None
    review_note: str | None
    # A reviewer accepted or corrected this coding (REQ-REV-004).
    reviewed: bool = False


class CodingsInForce:
    """Published reader: codings of given invoice lines, with their reviews applied.

    Example:
        codings = await CodingsInForce(codings_reader, reviews).read(connection, line_ids)
    """

    def __init__(self, codings: CodingsReader, reviews: ReviewRepositoryPort) -> None:
        self._codings = codings
        self._reviews = reviews

    async def read(
        self, connection: AsyncConnection, invoice_line_ids: list[str]
    ) -> dict[str, CodingInForce]:
        """Return, by invoice line identifier, the coding in force of each coded line.

        Example:
            (await codings.read(connection, ["9b1c..."]))["9b1c..."].item_number
        """
        codings = await self._codings.read_codings(connection, invoice_line_ids)
        encoded_ids = [coding.encoded_line_id for coding in codings.values()]
        reviews = await self._reviews.read_reviews(connection, encoded_ids)
        return {
            line_id: in_force(coding, reviews.get(coding.encoded_line_id))
            for line_id, coding in codings.items()
        }


def in_force(coding: LineCoding, review: LineReview | None) -> CodingInForce:
    """Apply a review, when there is one, to the coding the system recorded.

    Example:
        in_force(coding, None).item_number == coding.item_number
    """
    return CodingInForce(
        encoded_line_id=coding.encoded_line_id,
        target_sheet=coding.target_sheet,
        item_number=review.item_number if review else coding.item_number,
        catalog_description=review.catalog_description if review else coding.catalog_description,
        confidence=coding.confidence,
        review_status=review.review_status.value if review else coding.review_status,
        flags=coding.flags,
        note=coding.note,
        review_note=review.note if review else None,
        reviewed=review is not None,
    )
