"""The items a reviewer can choose for a line (REQ-REV-001, REQ-REV-002, D-3.16).

The whole target sheet, best lexical score first, with the model's choice marked: the
reviewer sees what the model saw, and nothing from the other sheet.
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine

from sextante.catalog.contracts import Catalog, ItemNumber
from sextante.ingestion.contracts import JobLinesReader
from sextante.matching.contracts import CodingsReader, LineCandidates
from sextante.platform.errors import DomainError


class InvoiceLineNotFoundError(DomainError):
    """No coded line of this invoice has this identifier."""

    user_message_key = "errors.invoice_line.not_found"


@dataclass(frozen=True, slots=True)
class Candidate:
    """One item of the line's target sheet, as offered to the reviewer."""

    item_number: str
    description_pt: str
    description_en: str
    score: float
    rank: int
    chosen_by_model: bool


@dataclass(frozen=True, slots=True)
class LineCandidatesView:
    """The target sheet of the line and its items, best first."""

    target_sheet: str | None
    candidates: tuple[Candidate, ...]


class ReadLineCandidates:
    """Return the candidates of one coded line of one invoice.

    Example:
        view = await ReadLineCandidates(engine, lines, codings, catalog).execute(inv_id, line_id)
    """

    def __init__(
        self,
        engine: AsyncEngine,
        lines_reader: JobLinesReader,
        codings_reader: CodingsReader,
        catalog: Catalog,
    ) -> None:
        self._engine = engine
        self._lines_reader = lines_reader
        self._codings_reader = codings_reader
        self._catalog = catalog

    async def execute(self, invoice_id: str, invoice_line_id: str) -> LineCandidatesView:
        """Return the line's sheet and candidates. A line without sheet has none.

        Raises:
            InvoiceLineNotFoundError: when the line is not a coded line of this invoice.
        """
        async with self._engine.connect() as connection:
            owned = await self._lines_reader.line_belongs_to_invoice(
                connection, invoice_id, invoice_line_id
            )
            scored = (
                await self._codings_reader.read_candidates(connection, invoice_line_id)
                if owned
                else None
            )
        if scored is None:
            raise InvoiceLineNotFoundError(
                f"Line {invoice_line_id!r} is not a coded line of invoice {invoice_id!r}."
            )
        return LineCandidatesView(scored.target_sheet, self._offered(scored))

    def _offered(self, scored: LineCandidates) -> tuple[Candidate, ...]:
        offered = []
        for candidate in scored.candidates:
            catalog_item = self._catalog.find(ItemNumber(candidate.item_number))
            # Scores are of the catalog the line was coded with; an item since removed
            # from the catalog cannot be chosen, so it is not offered.
            if catalog_item is not None:
                offered.append(
                    Candidate(
                        item_number=candidate.item_number,
                        description_pt=catalog_item.description_pt,
                        description_en=catalog_item.description_en,
                        score=candidate.score,
                        rank=candidate.rank,
                        chosen_by_model=candidate.item_number == scored.chosen_item_number,
                    )
                )
        return tuple(offered)
