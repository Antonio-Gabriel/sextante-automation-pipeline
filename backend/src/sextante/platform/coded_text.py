"""A stable code with its text in the request's language, as the API returns it."""

from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict

from sextante.platform.language import Language
from sextante.platform.user_messages import has_user_message, user_message


class FlagResponse(BaseModel):
    """A flag, a note or a reason: the stable code and its text (REQ-CNF-004)."""

    model_config = ConfigDict(frozen=True)

    code: str
    message: str


UNDESCRIBED_KEY = "reasons.undescribed"


def coded_text(group: str, code: str | None, language: Language) -> FlagResponse | None:
    """The code with its text from the catalog group; None only when there is no code.

    A code without text is still shown, with a text that says so: a reason is never
    dropped because the catalog lacks it.

    Example:
        coded_text("flags", "entity_similar_not_equal", Language.EN)  # FlagResponse(...)
    """
    if code is None:
        return None
    return FlagResponse(code=code, message=_text(group, code, language))


def coded_texts(group: str, codes: Iterable[str], language: Language) -> list[FlagResponse]:
    """Each code with its text, as coded_text gives it; an unknown code says so, never fails.

    Example:
        coded_texts("flags", ("fallback_applied",), Language.EN)
    """
    return [FlagResponse(code=c, message=_text(group, c, language)) for c in codes]


def _text(group: str, code: str, language: Language) -> str:
    key = f"{group}.{code}"
    return user_message(key if has_user_message(key) else UNDESCRIBED_KEY, language)
