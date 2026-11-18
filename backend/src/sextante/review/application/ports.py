"""Ports of the review module (02-arquitectura.md §4)."""

from datetime import datetime
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.review.domain.review_state import LineReview


class ReviewRepositoryPort(Protocol):
    """Persistence of the review state of coded lines."""

    async def read_reviews(
        self, connection: AsyncConnection, encoded_line_ids: list[str]
    ) -> dict[str, LineReview]:
        """Return the review of each given coded line that has one, by its identifier."""
        ...

    async def save_review(
        self, connection: AsyncConnection, review: LineReview, reviewed_by: str, at: datetime
    ) -> None:
        """Insert or replace the review in force of one coded line."""
        ...
