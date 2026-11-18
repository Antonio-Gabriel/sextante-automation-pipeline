"""Published contract of the matching module (02-arquitectura.md §2.1)."""

from sextante.matching.application.ports import (
    CodingsReader,
    ItemClassifier,
    ItemClassifierUnavailableError,
    LexicalScorer,
    TokenUsageReader,
)
from sextante.matching.application.records import LineCandidates, LineCoding, ScoredCandidate
from sextante.matching.domain.entity_check import (
    REVIEWER_RESOLUTION_REASON,
    EntityCheckResult,
    EntityDenylist,
    EntityVerdict,
    TargetEntity,
    check_billed_entity,
    entity_notes,
    exact_entity_match_label,
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
    "REVIEWER_RESOLUTION_REASON",
    "CandidateItem",
    "CodingsReader",
    "Confidence",
    "EntityCheckResult",
    "EntityDenylist",
    "EntityVerdict",
    "FlagReason",
    "InvoiceContext",
    "ItemChoiceFromModel",
    "ItemChoiceRequest",
    "ItemChoiceResponse",
    "ItemClassifier",
    "ItemClassifierUnavailableError",
    "LexicalScore",
    "LexicalScorer",
    "LineCandidates",
    "LineCoding",
    "LineToCode",
    "ScoredCandidate",
    "TargetEntity",
    "TokenUsageReader",
    "check_billed_entity",
    "entity_notes",
    "exact_entity_match_label",
    "target_sheet_for",
]
