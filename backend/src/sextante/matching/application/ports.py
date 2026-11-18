"""Ports of the matching use cases (02-arquitectura.md §2.3)."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from sextante.catalog.contracts import CatalogItem
from sextante.matching.domain.item_choice import ItemChoiceRequest, ItemChoiceResponse

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncConnection

    from sextante.matching.application.records import EncodedLineRecord, LineCoding, ModelCallRecord


@dataclass(frozen=True, slots=True)
class LexicalScore:
    """Similarity of one line to one catalog item, and the item's rank for that line."""

    item_number: str
    score: float
    rank: int


class LexicalScorer(Protocol):
    """Port: score one line against every item of the target sheet (REQ-MAP-004)."""

    def score(
        self, description: str, catalog_items: Sequence[CatalogItem]
    ) -> tuple[LexicalScore, ...]:
        """Return one score per item, ranked best first."""
        ...


class ItemClassifier(Protocol):
    """Port: choose one item of the target sheet per line, or none (REQ-MAP-005, SEC-14)."""

    async def choose(self, request: ItemChoiceRequest) -> ItemChoiceResponse:
        """Answer with indexes into the request's list. Never with codes."""
        ...


class CodingsReader(Protocol):
    """Port, published to other modules: the coding of given invoice lines."""

    async def read_codings(
        self, connection: "AsyncConnection", line_ids: Sequence[str]
    ) -> dict[str, "LineCoding"]:
        """Return the coding of each line that has one, keyed by invoice line id."""
        ...


class MatchingRepositoryPort(Protocol):
    """Port: persistence of model calls, lexical scores and encoded lines."""

    async def record_model_call(
        self, connection: "AsyncConnection", record: "ModelCallRecord"
    ) -> None:
        """Insert the model call row."""
        ...

    async def record_encoded_line(
        self, connection: "AsyncConnection", record: "EncodedLineRecord"
    ) -> None:
        """Insert the encoded line and the lexical scores of every item of its sheet."""
        ...
