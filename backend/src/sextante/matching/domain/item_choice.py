"""What the item classifier is asked and what it may answer (SEC-14, REQ-MAP-005)."""

from dataclasses import dataclass
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from sextante.platform.limits import MAX_LINES_PER_INVOICE, MAX_RATIONALE_LENGTH, MAX_SHEET_ITEMS


@dataclass(frozen=True, slots=True)
class LineToCode:
    """One service line sent to the model: its position and description."""

    position: int
    description: str


@dataclass(frozen=True, slots=True)
class CandidateItem:
    """One item of the target sheet as shown to the model, with its index in the list."""

    index: int
    item_number: str
    description_pt: str
    description_en: str


@dataclass(frozen=True, slots=True)
class InvoiceContext:
    """Invoice data that helps read short line descriptions. External content (SEC-14)."""

    supplier_name: str | None
    currency: str | None


@dataclass(frozen=True, slots=True)
class ItemChoiceRequest:
    """One call per invoice: its context, service lines and the whole target sheet (D-3.16)."""

    context: InvoiceContext
    lines: tuple[LineToCode, ...]
    candidates: tuple[CandidateItem, ...]


class ItemChoiceFromModel(BaseModel):
    """One line decision returned by the model. Validated before any use (SEC-09.2, SEC-14).

    The model answers with an index into the server's list, or None. Never a code.

    Example:
        ItemChoiceFromModel(line_position=1, candidate_index=0)
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    line_position: Annotated[int, Field(ge=1, le=MAX_LINES_PER_INVOICE)]
    candidate_index: Annotated[int, Field(ge=0, lt=MAX_SHEET_ITEMS)] | None
    rationale: Annotated[str, Field(max_length=MAX_RATIONALE_LENGTH)] = ""


@dataclass(frozen=True, slots=True)
class ItemChoiceResponse:
    """The model's answers, with what is needed to explain and cost the call (REQ-AUD-003/004)."""

    choices: tuple[ItemChoiceFromModel, ...]
    model_id: str
    prompt_version: str
    input_tokens: int
    output_tokens: int
    # Input written to and read from the prompt cache; input_tokens excludes both.
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
