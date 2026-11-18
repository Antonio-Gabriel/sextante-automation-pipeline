"""Published contract of the matching module (02-arquitectura.md §2.1)."""

from sextante.matching.application.ports import CodingsReader, ItemClassifier, LexicalScorer
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
from sextante.matching.domain.line_decision import Confidence, FlagReason
from sextante.matching.domain.routing import target_sheet_for
from sextante.matching.domain.scoring import LexicalScore

__all__ = [
    "AmbiguityReason",
    "CandidateItem",
    "CodingsReader",
    "Confidence",
    "EntityCheckResult",
    "EntityVerdict",
    "FlagReason",
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
