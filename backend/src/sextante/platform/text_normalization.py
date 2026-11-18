"""The single home of text normalization (04-padroes-de-codigo.md §1.5).

Comparison normalization is applied to text that is scored or compared, never displayed.
Input normalization of external text (SEC-09.3) joins this module with the first ticket
that persists invoice text.
"""

import re
import unicodedata
from typing import Final

_WHITESPACE_RUN: Final = re.compile(r"\s+")
_INVISIBLE_CATEGORIES: Final = frozenset({"Cc", "Cf"})
_NON_BREAKING_SPACE: Final = "\xa0"


def normalize_for_comparison(value: str) -> str:
    """Fold compatibility forms, drop invisible characters and collapse whitespace.

    NFKC turns a non-breaking space into a plain space; format characters such as the
    zero-width space found in the real catalog (D-3.9) are dropped.

    Example:
        normalize_for_comparison(" Sea \\u200bPassage  Ticket")  # "Sea Passage Ticket"
    """
    folded = unicodedata.normalize("NFKC", value)
    visible = "".join(character for character in folded if not _is_invisible(character))
    return _WHITESPACE_RUN.sub(" ", visible).strip()


def has_invisible_characters(value: str) -> bool:
    """Tell whether the text holds control or format characters, or non-breaking spaces.

    Example:
        has_invisible_characters("Certificado\\xa0de")  # True
    """
    return any(_is_invisible(character) or character == _NON_BREAKING_SPACE for character in value)


def _is_invisible(character: str) -> bool:
    return unicodedata.category(character) in _INVISIBLE_CATEGORIES
