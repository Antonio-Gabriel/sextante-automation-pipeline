"""The item classifier behind the model call ceiling (SEC-12)."""

from sextante.matching.application.ports import ItemClassifier
from sextante.matching.domain.item_choice import ItemChoiceRequest, ItemChoiceResponse
from sextante.platform.model_call_ceiling import ModelCallCeiling


class CeilingItemClassifier:
    """ItemClassifier that takes room under the ceiling before every call, retries included.

    Example:
        classifier = CeilingItemClassifier(ClaudeItemClassifier(client, model_id), ceiling)
    """

    def __init__(self, classifier: ItemClassifier, ceiling: ModelCallCeiling) -> None:
        self._classifier = classifier
        self._ceiling = ceiling

    async def choose(self, request: ItemChoiceRequest) -> ItemChoiceResponse:
        """Wait for room under the ceiling, then ask the classifier."""
        await self._ceiling.acquire()
        return await self._classifier.choose(request)
