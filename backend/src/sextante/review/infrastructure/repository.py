"""SQLite persistence of the review state (REQ-REV-004, REQ-REV-005)."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.review.domain.review_state import LineReview, ReviewStatus
from sextante.review.infrastructure.tables import LINE_REVIEW_TABLE


class ReviewRepository:
    """Reads and writes line_review. The coding record in encoded_line is never touched.

    Example:
        reviews = await ReviewRepository().read_reviews(connection, ["3f2a..."])
    """

    async def read_reviews(
        self, connection: AsyncConnection, encoded_line_ids: list[str]
    ) -> dict[str, LineReview]:
        """Return the review of each given coded line that has one, by its identifier."""
        if not encoded_line_ids:
            return {}
        table = LINE_REVIEW_TABLE
        query = select(table).where(table.c.encoded_line_id.in_(encoded_line_ids))
        rows = (await connection.execute(query)).all()
        return {
            str(r.encoded_line_id): LineReview(
                encoded_line_id=str(r.encoded_line_id),
                review_status=ReviewStatus(str(r.review_status)),
                item_number=r.item_number,
                catalog_description=r.catalog_description,
                note=r.note,
            )
            for r in rows
        }

    async def save_review(
        self, connection: AsyncConnection, review: LineReview, reviewed_by: str, at: datetime
    ) -> None:
        """Insert or replace the review in force; its history is in audit_event (REQ-REV-004)."""
        values = {
            "review_status": review.review_status.value,
            "item_number": review.item_number,
            "catalog_description": review.catalog_description,
            "note": review.note,
            "reviewed_by": reviewed_by,
            "reviewed_at": at.isoformat(),
        }
        statement = insert(LINE_REVIEW_TABLE).values(
            encoded_line_id=review.encoded_line_id, **values
        )
        await connection.execute(
            statement.on_conflict_do_update(index_elements=["encoded_line_id"], set_=values)
        )
