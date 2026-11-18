"""Records written by the encoding use case through its repository port."""

from dataclasses import dataclass
from datetime import datetime

from sextante.catalog.contracts import TargetSheet
from sextante.matching.application.ports import LexicalScore
from sextante.matching.domain.choice_resolution import LineChoice
from sextante.matching.domain.item_choice import ItemChoiceResponse


@dataclass(frozen=True, slots=True)
class ModelCallRecord:
    """One paid model call and what it cost (REQ-AUD-003, REQ-AUD-004)."""

    call_id: str
    invoice_id: str
    response: ItemChoiceResponse
    called_at: datetime


@dataclass(frozen=True, slots=True)
class EncodedLineRecord:
    """The decision for one line, with what produced it (REQ-AUD-001)."""

    encoded_line_id: str
    invoice_line_id: str
    target_sheet: TargetSheet
    choice: LineChoice
    scores: tuple[LexicalScore, ...]
    catalog_digest: str
    model_call_id: str
    encoded_at: datetime


@dataclass(frozen=True, slots=True)
class LineCoding:
    """The coding of one invoice line, as read for listings."""

    target_sheet: str
    item_number: str | None
    catalog_description: str | None
