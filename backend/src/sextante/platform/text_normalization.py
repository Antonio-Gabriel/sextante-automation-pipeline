"""The single home of text normalization (04-padroes-de-codigo.md §1.5).

Two normalizations live here, and only here:
- input normalization (SEC-09.3, REQ-ING-008), applied to external text before it is
  validated, persisted or compared;
- comparison normalization, applied to text that is scored or compared, never displayed.
"""

import re
import unicodedata
from typing import Final

_WHITESPACE_RUN: Final = re.compile(r"\s+")
_NON_WORD_RUN: Final = re.compile(r"[^\w]+")
_INVISIBLE_CATEGORIES: Final = frozenset({"Cc", "Cf"})
_NON_BREAKING_SPACE: Final = "\xa0"


def normalize_text_input(value: str) -> str:
    """Normalize to NFC and strip control and format characters, keeping tabs and newlines.

    Example:
        normalize_text_input("Taxa\\u0000 de movimentação")  # "Taxa de movimentação"
    """
    return "".join(
        character
        for character in unicodedata.normalize("NFC", value)
        if not _is_invisible(character) or character in "\n\t"
    )


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


def fold_for_matching(value: str) -> str:
    """Comparison text without accents, punctuation or case, as words separated by one space.

    Used where minor spelling differences must not count, such as the billed entity
    (R5, REQ-ENT-002).

    Example:
        fold_for_matching("Transitários, Lda.")  # "transitarios lda"
    """
    decomposed = unicodedata.normalize("NFKD", normalize_for_comparison(value))
    unaccented = "".join(c for c in decomposed if not unicodedata.combining(c))
    return _WHITESPACE_RUN.sub(" ", _NON_WORD_RUN.sub(" ", unaccented.casefold())).strip()


def has_invisible_characters(value: str) -> bool:
    """Tell whether the text holds control or format characters, or non-breaking spaces.

    Example:
        has_invisible_characters("Certificado\\xa0de")  # True
    """
    return any(_is_invisible(character) or character == _NON_BREAKING_SPACE for character in value)


def _is_invisible(character: str) -> bool:
    return unicodedata.category(character) in _INVISIBLE_CATEGORIES
