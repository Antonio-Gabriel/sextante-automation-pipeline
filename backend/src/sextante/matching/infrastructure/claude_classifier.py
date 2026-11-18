"""ItemClassifier adapter on the Anthropic API (ticket 11, SEC-14, REQ-MAP-005).

One call per invoice. The model answers, per line, an index into the server's list of
candidates, or null; never an item number, a confidence or an explanation. The answer is
JSON constrained by a declared schema (``output_config.format``), and the use case
validates it again before any effect.

Configuration approved on 2026-11-18 (00-decisoes-e-lacunas.md §3.22): no sampling
parameter, which the API refuses on every model; a schema-constrained output instead of a
forced tool, which current models refuse; low effort; server-side fallbacks on a refusal.
"""

import json
import logging
from typing import Any, Final

from anthropic import APIConnectionError, APIStatusError, AsyncAnthropic
from anthropic.types.beta import BetaMessage
from pydantic import ValidationError

from sextante.matching.application.ports import ItemClassifierUnavailableError
from sextante.matching.domain.item_choice import (
    ItemChoiceFromModel,
    ItemChoiceRequest,
    ItemChoiceResponse,
)
from sextante.prompts import ITEM_CHOICE_PROMPT_VERSION, item_choice_prompt

logger = logging.getLogger(__name__)

# Thinking is always on in the current models and counts against max_tokens, so the
# budget has a fixed part for it and a part per line for the answer (REQ-MAP-005).
BASE_MAX_TOKENS: Final = 2048
MAX_TOKENS_PER_LINE: Final = 64
EFFORT: Final = "low"
FALLBACK_BETA: Final = "server-side-fallback-2026-07-01"
# One invoice is one call; a call that takes longer is treated as unavailable.
MODEL_TIMEOUT_SECONDS: Final = 120.0
# Timeout, conflict, rate limit and 5xx are transient: the use case retries them with
# backoff (REQ-PLT-003). Any other refusal would fail the same way again.
TRANSIENT_STATUSES: Final = frozenset({408, 409, 429})
SERVER_ERROR: Final = 500

ANSWER_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "properties": {
        "choices": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "line_position": {"type": "integer"},
                    "candidate_index": {"type": ["integer", "null"]},
                },
                "required": ["line_position", "candidate_index"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["choices"],
    "additionalProperties": False,
}


def create_model_client(api_key: str) -> AsyncAnthropic:
    """The API client for the item choice: it never retries by itself.

    The use case retries transient failures with its own backoff and attempt count, so
    a call is never retried twice over (REQ-PLT-003).

    Example:
        client = create_model_client(settings.anthropic_api_key.get_secret_value())
    """
    return AsyncAnthropic(api_key=api_key, max_retries=0, timeout=MODEL_TIMEOUT_SECONDS)


class ClaudeItemClassifier:
    """ItemClassifier that asks Claude for one candidate index per service line.

    Example:
        classifier = ClaudeItemClassifier(AsyncAnthropic(api_key=key, max_retries=0), model_id)
        response = await classifier.choose(request)
    """

    def __init__(self, client: AsyncAnthropic, model_id: str) -> None:
        self._client = client
        self._model_id = model_id
        self._system = item_choice_prompt()

    async def choose(self, request: ItemChoiceRequest) -> ItemChoiceResponse:
        """Ask for the invoice's lines in one call and return the parsed answers.

        An answer that cannot be read (a refusal, a cut answer, broken JSON) comes back
        with no choices, so every line is recorded as an invalid response, LOW and
        flagged; it is never retried and never filled with a default.

        Example:
            (await classifier.choose(request)).choices[0].candidate_index

        Raises:
            ItemClassifierUnavailableError: on a network failure, a timeout, 429 or 5xx.
        """
        try:
            message = await self._create(request)
        except (APIConnectionError, APIStatusError) as error:
            raise _unavailable_or_final(error) from None
        return ItemChoiceResponse(
            choices=_choices(message),
            model_id=message.model,
            prompt_version=ITEM_CHOICE_PROMPT_VERSION,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )

    async def _create(self, request: ItemChoiceRequest) -> BetaMessage:
        return await self._client.beta.messages.create(
            model=self._model_id,
            max_tokens=BASE_MAX_TOKENS + MAX_TOKENS_PER_LINE * len(request.lines),
            system=self._system,
            messages=[{"role": "user", "content": invoice_data(request)}],
            output_config={
                "effort": EFFORT,
                "format": {"type": "json_schema", "schema": ANSWER_SCHEMA},
            },
            betas=[FALLBACK_BETA],
            fallbacks="default",
        )


def _unavailable_or_final(error: APIConnectionError | APIStatusError) -> Exception:
    # No answer, a timeout, a conflict, a rate limit or a 5xx is transient: the use case
    # retries it. Any other refusal would fail the same way again, so it stays as it is.
    if isinstance(error, APIConnectionError):
        return ItemClassifierUnavailableError(
            f"Model call failed with {type(error).__name__}, no answer. "
            "Expected an answer; the call is retried."
        )
    if error.status_code in TRANSIENT_STATUSES or error.status_code >= SERVER_ERROR:
        return ItemClassifierUnavailableError(
            f"Model call failed with status {error.status_code}. Expected 200; the call is retried."
        )
    return error


def invoice_data(request: ItemChoiceRequest) -> str:
    """The user message: the invoice as JSON, delimited, never mixed with instructions.

    ``<`` is written as ``\\u003c``, so no description can close the delimiter (SEC-14).

    Example:
        invoice_data(request)  # "<invoice_data>\\n{...}\\n</invoice_data>"
    """
    payload = {
        "invoice": {
            "supplier": request.context.supplier_name,
            "currency": request.context.currency,
        },
        "lines": [
            {"position": line.position, "description": line.description} for line in request.lines
        ],
        "candidates": [
            {
                "index": c.index,
                "item_number": c.item_number,
                "description_pt": c.description_pt,
                "description_en": c.description_en,
            }
            for c in request.candidates
        ],
    }
    text = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    return f"<invoice_data>\n{text}\n</invoice_data>"


def _choices(message: BetaMessage) -> tuple[ItemChoiceFromModel, ...]:
    # Only the stop reason and the error type are logged: never the answer, which may
    # echo invoice text (SEC-15).
    if message.stop_reason != "end_turn":
        logger.warning("model_answer_unusable", extra={"stop_reason": message.stop_reason})
        return ()
    text = next((block.text for block in message.content if block.type == "text"), "")
    try:
        entries = json.loads(text)["choices"]
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        logger.warning("model_answer_unusable", extra={"error_type": type(error).__name__})
        return ()
    return tuple(choice for choice in map(_choice, entries) if choice is not None)


def _choice(entry: object) -> ItemChoiceFromModel | None:
    # An entry outside the schema is dropped alone: its line becomes an invalid response,
    # the other lines keep their answers (REQ-MAP-007).
    try:
        return ItemChoiceFromModel.model_validate(entry)
    except ValidationError:
        logger.warning("model_answer_rejected_by_schema", extra={"error_type": "ValidationError"})
        return None
