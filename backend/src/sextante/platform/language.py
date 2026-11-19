"""The languages of the texts shown to people: English by default, Portuguese on request.

Decision 3.25 (docs/00) revises R12: the interface is in English by default, with
Portuguese available. Codes, identifiers and logs stay in English whatever the language.
"""

import math
from enum import StrEnum
from typing import Final


class Language(StrEnum):
    """A language the interface and the API texts are offered in."""

    EN = "en"
    PT = "pt"


DEFAULT_LANGUAGE: Final = Language.EN
# An Accept-Language header longer than this is not parsed: it is not a real browser's.
MAX_ACCEPT_LANGUAGE_LENGTH: Final = 256


def parse_accept_language(header: str | None) -> Language:
    """The first supported language of an Accept-Language header, in its order of quality.

    Anything unknown, malformed or missing gives the default, English.

    Example:
        parse_accept_language("pt-PT,pt;q=0.9,en;q=0.8")  # Language.PT
    """
    if not header or len(header) > MAX_ACCEPT_LANGUAGE_LENGTH:
        return DEFAULT_LANGUAGE
    ranked = sorted((_ranked_tag(part) for part in header.split(",")), key=lambda tag: -tag[1])
    supported = {language.value: language for language in Language}
    # q=0 means "not this one" (RFC 9110 §12.4.2).
    accepted = (tag for tag, quality in ranked if quality > 0 and tag in supported)
    return next((supported[tag] for tag in accepted), DEFAULT_LANGUAGE)


def _ranked_tag(part: str) -> tuple[str, float]:
    # "pt-PT;q=0.9" -> ("pt", 0.9); a malformed or out-of-range quality counts as 0.
    tag, _, parameters = part.strip().partition(";")
    quality = 1.0
    if parameters.strip().startswith("q="):
        try:
            quality = float(parameters.strip()[2:])
        except ValueError:
            quality = 0.0
    if not (math.isfinite(quality) and 0.0 <= quality <= 1.0):
        quality = 0.0
    return tag.split("-")[0].strip().lower(), quality
