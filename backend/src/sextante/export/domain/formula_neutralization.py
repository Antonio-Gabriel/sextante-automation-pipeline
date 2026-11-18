"""The single point of formula neutralization for every export (SEC-17, REQ-EXP-003)."""

from typing import Final

FORMULA_TRIGGERS: Final = ("=", "+", "-", "@", "\t", "\r")


def neutralize_formula(value: str) -> str:
    """Prefix a leading formula trigger so spreadsheets treat the cell as text.

    Applies to every text cell of every export, because any of them may carry content
    extracted from a supplier invoice.

    Example:
        neutralize_formula("=HYPERLINK(...)")  # "'=HYPERLINK(...)"
    """
    if value.startswith(FORMULA_TRIGGERS):
        return f"'{value}"
    return value
