"""A stable code with its Portuguese text, as the API returns it (REQ-PLT-006)."""

from pydantic import BaseModel, ConfigDict

from sextante.platform.user_messages import USER_MESSAGES_PT


class FlagResponse(BaseModel):
    """A flag, a note or a reason: the stable code and its Portuguese text (REQ-CNF-004)."""

    model_config = ConfigDict(frozen=True)

    code: str
    message: str


UNDESCRIBED_KEY = "reasons.undescribed"


def coded_text(group: str, code: str | None) -> FlagResponse | None:
    """The code with its text from the catalog group; None only when there is no code.

    A code without text is still shown, with a text that says so: a reason is never
    dropped because the catalog lacks it.

    Example:
        coded_text("flags", "entity_similar_not_equal")  # FlagResponse(code=..., message=...)
    """
    if code is None:
        return None
    message = USER_MESSAGES_PT.get(f"{group}.{code}", USER_MESSAGES_PT[UNDESCRIBED_KEY])
    return FlagResponse(code=code, message=message)
