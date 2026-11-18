"""Records written by the encoding use case through its repository port."""

from dataclasses import dataclass
from datetime import datetime

from sextante.catalog.contracts import TargetSheet
from sextante.matching.domain.choice_resolution import LineChoice
from sextante.matching.domain.item_choice import ItemChoiceResponse
from sextante.matching.domain.line_decision import LineDecision
from sextante.matching.domain.scoring import LexicalScore


@dataclass(frozen=True, slots=True)
class ModelCallRecord:
    """One paid model call and what it cost (REQ-AUD-003, REQ-AUD-004)."""

    call_id: str
    invoice_id: str
    response: ItemChoiceResponse
    called_at: datetime


@dataclass(frozen=True, slots=True)
class EncodedLineRecord:
    """The decision for one line, with what produced it (REQ-AUD-001).

    ``target_sheet`` and ``model_call_id`` are None for the lines of an ambiguous invoice,
    which are recorded uncoded (D-3.15).
    """

    encoded_line_id: str
    invoice_line_id: str
    target_sheet: TargetSheet | None
    choice: LineChoice | None
    decision: LineDecision
    scores: tuple[LexicalScore, ...]
    catalog_digest: str
    model_call_id: str | None
    encoded_at: datetime


@dataclass(frozen=True, slots=True)
class LineCoding:
    """The coding of one invoice line, as read for listings."""

    encoded_line_id: str
    invoice_line_id: str
    target_sheet: str | None
    item_number: str | None
    catalog_description: str | None
    confidence: str
    review_status: str
    flags: tuple[str, ...]
    note: str | None


@dataclass(frozen=True, slots=True)
class ScoredCandidate:
    """One item of the target sheet with its lexical score and rank for a line."""

    item_number: str
    score: float
    rank: int


@dataclass(frozen=True, slots=True)
class LineCandidates:
    """The scored items of a line's target sheet and the model's choice (REQ-REV-001)."""

    target_sheet: str | None
    chosen_item_number: str | None
    candidates: tuple[ScoredCandidate, ...]


@dataclass(frozen=True, slots=True)
class CodingsSummary:
    """What coded some lines until now, before a new coding takes over (NFR-REL-002)."""

    prompt_versions: tuple[str, ...]
    catalog_digests: tuple[str, ...]
    line_count: int


@dataclass(frozen=True, slots=True)
class CodingHistoryEntry:
    """One coding of a line, in force or superseded, with what produced it (NFR-REL-002)."""

    encoded_line_id: str
    item_number: str | None
    catalog_description: str | None
    confidence: str
    prompt_version: str | None
    model_id: str | None
    catalog_digest: str
    encoded_at: str
    superseded_at: str | None
