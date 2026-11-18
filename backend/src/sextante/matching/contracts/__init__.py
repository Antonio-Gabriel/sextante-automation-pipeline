"""Published contract of the matching module (02-arquitectura.md §2.1)."""

from sextante.matching.application.ports import ItemClassifier, LexicalScore, LexicalScorer
from sextante.matching.domain.item_choice import (
    CandidateItem,
    ItemChoiceFromModel,
    ItemChoiceRequest,
    ItemChoiceResponse,
    LineToCode,
)

__all__ = [
    "CandidateItem",
    "ItemChoiceFromModel",
    "ItemChoiceRequest",
    "ItemChoiceResponse",
    "ItemClassifier",
    "LexicalScore",
    "LexicalScorer",
    "LineToCode",
]
