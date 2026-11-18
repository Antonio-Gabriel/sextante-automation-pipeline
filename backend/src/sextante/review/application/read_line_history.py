"""Every coding of a line, with its review: the earlier ones stay consultable (ticket 14).

A coding superseded by a recoding is never shown as in force, but it is never lost
either: it keeps the prompt version and catalog digest that produced it, and the review
a person made of it (NFR-REL-002, D-3.23).
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine

from sextante.ingestion.contracts import JobLinesReader
from sextante.matching.contracts import CodingHistoryEntry, CodingsReader
from sextante.review.application.ports import ReviewRepositoryPort
from sextante.review.application.read_line_candidates import InvoiceLineNotFoundError
from sextante.review.domain.review_state import LineReview


@dataclass(frozen=True, slots=True)
class LineHistoryEntry:
    """One coding of the line and, when a person reviewed it, that review."""

    coding: CodingHistoryEntry
    review: LineReview | None


class ReadLineHistory:
    """Return the codings of one line of one invoice, the newest first.

    Example:
        entries = await ReadLineHistory(engine, lines, codings, reviews).execute(inv, line)
    """

    def __init__(
        self,
        engine: AsyncEngine,
        lines_reader: JobLinesReader,
        codings_reader: CodingsReader,
        reviews: ReviewRepositoryPort,
    ) -> None:
        self._engine = engine
        self._lines_reader = lines_reader
        self._codings_reader = codings_reader
        self._reviews = reviews

    async def execute(self, invoice_id: str, invoice_line_id: str) -> list[LineHistoryEntry]:
        """Return the line's codings, newest first, each with its review.

        Example:
            (await history.execute("3f2a...", "9b1c..."))[1].coding.superseded_at

        Raises:
            InvoiceLineNotFoundError: when the line is not a line of this invoice.
        """
        async with self._engine.connect() as connection:
            if not await self._lines_reader.line_belongs_to_invoice(
                connection, invoice_id, invoice_line_id
            ):
                raise InvoiceLineNotFoundError(
                    f"Line {invoice_line_id!r} is not a line of invoice {invoice_id!r}."
                )
            codings = await self._codings_reader.read_line_history(connection, invoice_line_id)
            ids = [coding.encoded_line_id for coding in codings]
            reviews = await self._reviews.read_reviews(connection, ids)
        return [LineHistoryEntry(c, reviews.get(c.encoded_line_id)) for c in codings]
