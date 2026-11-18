"""Ports of the matching use cases (02-arquitectura.md §2.3)."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol

from sextante.catalog.contracts import CatalogItem
from sextante.matching.domain.item_choice import ItemChoiceRequest, ItemChoiceResponse
from sextante.matching.domain.scoring import LexicalScore
from sextante.platform.errors import DomainError

if TYPE_CHECKING:
    from datetime import datetime

    from sqlalchemy.ext.asyncio import AsyncConnection

    from sextante.matching.application.records import (
        EncodedLineRecord,
        LineCandidates,
        LineCoding,
        ModelCallRecord,
    )


class LexicalScorer(Protocol):
    """Port: score one line against every item of the target sheet (REQ-MAP-004)."""

    def score(
        self, description: str, catalog_items: Sequence[CatalogItem]
    ) -> tuple[LexicalScore, ...]:
        """Return one score per item, ranked best first."""
        ...


class ItemClassifierUnavailableError(DomainError):
    """The model could not answer now (timeout, overload, network): worth retrying.

    Adapters raise this for transient failures only (REQ-PLT-003). Any other failure,
    including an answer that breaks the schema, is never retried.
    """

    user_message_key = "errors.internal"


class TokenUsageReader(Protocol):
    """Port, published to other modules: tokens spent on given invoices (REQ-AUD-004)."""

    async def read_token_usage(
        self, connection: "AsyncConnection", invoice_ids: Sequence[str]
    ) -> dict[str, tuple[int, int]]:
        """Return, by invoice, the input and output tokens of its model calls.

        An invoice without a model call is absent.
        """
        ...


class ItemClassifier(Protocol):
    """Port: choose one item of the target sheet per line, or none (REQ-MAP-005, SEC-14)."""

    async def choose(self, request: ItemChoiceRequest) -> ItemChoiceResponse:
        """Answer with indexes into the request's list. Never with codes."""
        ...


class CodingsReader(Protocol):
    """Port, published to other modules: the coding of given invoice lines."""

    async def read_encoded_line(
        self, connection: "AsyncConnection", encoded_line_id: str
    ) -> "LineCoding | None":
        """Return one coding by its own identifier, or None."""
        ...

    async def read_candidates(
        self, connection: "AsyncConnection", invoice_line_id: str
    ) -> "LineCandidates | None":
        """Return the scored items of the line's sheet and the model's choice, or None."""
        ...

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

    async def supersede_codings(
        self, connection: "AsyncConnection", invoice_line_ids: Sequence[str], at: "datetime"
    ) -> None:
        """Mark the codings in force of these lines as superseded; nothing is overwritten."""
        ...
