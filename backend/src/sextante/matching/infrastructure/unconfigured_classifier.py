"""Placeholder classifier until the Claude adapter lands (ticket 11)."""

from sextante.matching.domain.item_choice import ItemChoiceRequest, ItemChoiceResponse
from sextante.platform.errors import DomainError


class ItemClassifierNotConfiguredError(DomainError):
    """No item classifier is configured in this build."""

    user_message_key = "errors.internal"


class UnconfiguredItemClassifier:
    """Refuses to classify, so that no invoice is ever coded by an invented answer.

    Example:
        await UnconfiguredItemClassifier().choose(request)  # raises
    """

    async def choose(self, request: ItemChoiceRequest) -> ItemChoiceResponse:
        """Refuse: the Claude adapter is not wired yet."""
        raise ItemClassifierNotConfiguredError(
            "No item classifier is configured. Expected the Claude adapter of ticket 11."
        )
