"""Published contract of the matching module (02-arquitectura.md §2.1)."""

from sextante.matching.application.ports import (
    CodingsReader,
    ItemClassifier,
    LexicalScore,
    LexicalScorer,
)
from sextante.matching.application.records import LineCoding
from sextante.matching.domain.entity_check import (
    AmbiguityReason,
    EntityCheckResult,
    EntityVerdict,
    TargetEntity,
    check_billed_entity,
)
from sextante.matching.domain.item_choice import (
    CandidateItem,
    InvoiceContext,
    ItemChoiceFromModel,
    ItemChoiceRequest,
    ItemChoiceResponse,
    LineToCode,
)
from sextante.matching.domain.routing import target_sheet_for

__all__ = [
    "AmbiguityReason",
    "CandidateItem",
    "CodingsReader",
    "EntityCheckResult",
    "EntityVerdict",
    "InvoiceContext",
    "ItemChoiceFromModel",
    "ItemChoiceRequest",
    "ItemChoiceResponse",
    "ItemClassifier",
    "LexicalScore",
    "LexicalScorer",
    "LineCoding",
    "LineToCode",
    "TargetEntity",
    "check_billed_entity",
    "target_sheet_for",
]
