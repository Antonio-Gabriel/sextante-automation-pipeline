"""In-memory ItemClassifier for tests (04-padroes-de-codigo.md §3.3). Never calls a network."""

from collections.abc import Mapping, Sequence
from typing import Final

from sextante.matching.contracts import ItemChoiceFromModel, ItemChoiceRequest, ItemChoiceResponse

FAKE_MODEL_ID: Final = "fake-classifier"
FAKE_PROMPT_VERSION: Final = "item_choice.fake"


class FakeItemClassifier:
    """Answers with declared choices, by line position, and records every request.

    ``choices_by_item_number`` names the item to choose (None for "no item fits");
    ``raw_indexes`` gives the index as the model would, to exercise invalid answers. A
    position left out of both gets no answer at all.

    Example:
        classifier = FakeItemClassifier(choices_by_item_number={1: "O00004"})
    """

    def __init__(
        self,
        choices_by_item_number: Mapping[int, str | None] | None = None,
        raw_indexes: Mapping[int, int | None] | None = None,
        bypass_schema_with_index: int | None = None,
        failures: Sequence[Exception] = (),
    ) -> None:
        self._by_item_number = choices_by_item_number or {}
        self._raw_indexes = raw_indexes or {}
        self._bypass_index = bypass_schema_with_index
        # Raised one per call, in order, before any answer: simulates an unavailable model.
        self._failures = list(failures)
        self.calls: list[ItemChoiceRequest] = []

    async def choose(self, request: ItemChoiceRequest) -> ItemChoiceResponse:
        """Return the declared choices for the lines of this request."""
        self.calls.append(request)
        if self._failures:
            raise self._failures.pop(0)
        answered = [
            line.position
            for line in request.lines
            if self._answers(line.position) or self._bypass_index is not None
        ]
        choices = tuple(self._choice(position, request) for position in answered)
        return ItemChoiceResponse(
            choices=choices,
            model_id=FAKE_MODEL_ID,
            prompt_version=FAKE_PROMPT_VERSION,
            input_tokens=100 * len(request.lines),
            output_tokens=10 * len(request.lines),
        )

    def _choice(self, position: int, request: ItemChoiceRequest) -> ItemChoiceFromModel:
        if self._bypass_index is not None:
            # Simulates a careless adapter that skips validation (model_construct).
            return ItemChoiceFromModel.model_construct(
                line_position=position, candidate_index=self._bypass_index, rationale=""
            )
        return ItemChoiceFromModel(
            line_position=position, candidate_index=self._index(position, request)
        )

    def _answers(self, position: int) -> bool:
        return position in self._raw_indexes or position in self._by_item_number

    def _index(self, position: int, request: ItemChoiceRequest) -> int | None:
        if position in self._raw_indexes:
            return self._raw_indexes[position]
        wanted = self._by_item_number[position]
        if wanted is None:
            return None
        return next(c.index for c in request.candidates if c.item_number == wanted)
