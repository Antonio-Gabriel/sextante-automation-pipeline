"""Published contract of the matching module (02-arquitectura.md §2.1)."""

from sextante.matching.application.ports import (
    CodingsReader,
    ItemClassifier,
    LexicalScore,
    LexicalScorer,
)
from sextante.matching.application.records import LineCoding
from sextante.matching.domain.item_choice import (
    CandidateItem,
    InvoiceContext,
    ItemChoiceFromModel,
    ItemChoiceRequest,
    ItemChoiceResponse,
    LineToCode,
)

__all__ = [
    "CandidateItem",
    "CodingsReader",
    "InvoiceContext",
    "ItemChoiceFromModel",
    "ItemChoiceRequest",
    "ItemChoiceResponse",
    "ItemClassifier",
    "LexicalScore",
    "LexicalScorer",
    "LineCoding",
    "LineToCode",
]
