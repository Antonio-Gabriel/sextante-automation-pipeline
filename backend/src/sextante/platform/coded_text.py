"""A stable code with its Portuguese text, as the API returns it (REQ-PLT-006)."""

from pydantic import BaseModel, ConfigDict

from sextante.platform.user_messages import USER_MESSAGES_PT


class FlagResponse(BaseModel):
    """A flag, a note or a reason: the stable code and its Portuguese text (REQ-CNF-004)."""

    model_config = ConfigDict(frozen=True)

    code: str
    message: str


def coded_text(group: str, code: str | None) -> FlagResponse | None:
    """The code with its text from the catalog group, or None when there is no such text.

    Example:
        coded_text("flags", "entity_similar_not_equal")  # FlagResponse(code=..., message=...)
    """
    message = USER_MESSAGES_PT.get(f"{group}.{code}") if code else None
    return None if code is None or message is None else FlagResponse(code=code, message=message)
