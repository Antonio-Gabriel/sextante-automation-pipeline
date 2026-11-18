"""The single home of text normalization (04-padroes-de-codigo.md §1.5).

Two normalizations live here, and only here:
- input normalization (SEC-09.3), applied before validating or persisting external text;
- comparison normalization, applied to text that is scored or compared, never displayed.
"""

import re
import unicodedata
from typing import Final

_WHITESPACE_RUN: Final = re.compile(r"\s+")
_FORMAT_CHARACTER: Final = "Cf"
_CONTROL_CHARACTER: Final = "Cc"


def normalize_text_input(value: str) -> str:
    """Normalize to NFC and strip control and format characters, keeping tabs and newlines.

    Example:
        normalize_text_input("Taxa\\u0000 de movimentação")  # "Taxa de movimentação"
    """
    return "".join(
        character
        for character in unicodedata.normalize("NFC", value)
        if unicodedata.category(character) not in {_CONTROL_CHARACTER, _FORMAT_CHARACTER}
        or character in "\n\t"
    )


def normalize_for_comparison(value: str) -> str:
    """Fold compatibility forms, drop invisible characters and collapse whitespace.

    NFKC turns a non-breaking space into a plain space; format characters such as the
    zero-width space found in the real catalog (D-3.9) are dropped.

    Example:
        normalize_for_comparison(" Sea \\u200bPassage  Ticket")  # "Sea Passage Ticket"
    """
    folded = unicodedata.normalize("NFKC", value)
    visible = "".join(
        character
        for character in folded
        if unicodedata.category(character) not in {_CONTROL_CHARACTER, _FORMAT_CHARACTER}
    )
    return _WHITESPACE_RUN.sub(" ", visible).strip()


def has_invisible_characters(value: str) -> bool:
    """Tell whether the text holds control or format characters, or non-breaking spaces.

    Example:
        has_invisible_characters("Certificado\\xa0de")  # True
    """
    return any(
        unicodedata.category(character) in {_CONTROL_CHARACTER, _FORMAT_CHARACTER}
        or character == "\xa0"
        for character in value
    )
