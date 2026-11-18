"""Classify each invoice line as service, tax or discount (REQ-ING-006, D-3.17, L-06).

A line is VAT, or a discount, only when it names VAT or a discount and every one of its
words belongs to that vocabulary. "Taxa de pilotagem", customs duties, "Vat handling
fee" and a service that mentions "(isento de IVA)" all stay services: a service wrongly
taken for VAT would never be coded, which is the worse mistake (D-3.17).

Position in the table is handled upstream: the extractor already keeps subtotal and
total rows out of the lines (D-3.6).
"""

import re
from enum import StrEnum
from typing import Final

from sextante.platform.text_normalization import fold_for_matching

VAT_MARKER: Final = re.compile(
    r"\b(iva|vat|i v a|value added tax|imposto (sobre|s) (o )?valor acrescentado)\b"
)
VAT_VOCABULARY: Final = frozenset(
    {
        "iva",
        "vat",
        "i",
        "v",
        "a",
        "value",
        "added",
        "tax",
        "imposto",
        "sobre",
        "s",
        "o",
        "valor",
        "acrescentado",
        "do",
        "de",
        "total",
        "regime",
        "geral",
    }
)
DISCOUNT_MARKER: Final = re.compile(r"\b(desconto|descontos|desc|discount|discounts|abatimento)\b")
DISCOUNT_VOCABULARY: Final = frozenset(
    {
        "desconto",
        "descontos",
        "desc",
        "discount",
        "discounts",
        "abatimento",
        "comercial",
        "financeiro",
        "de",
        "do",
        "por",
        "pronto",
        "pagamento",
        "trade",
        "early",
        "payment",
    }
)
_NUMBER_OR_PERCENT: Final = re.compile(r"^\d+$")


class LineType(StrEnum):
    """Kind of an invoice line. Only services are coded (REQ-ING-006)."""

    SERVICE = "service"
    TAX = "tax"
    DISCOUNT = "discount"


def classify_line_type(description: str) -> LineType:
    """Return the line type; anything not recognised as tax or discount is a service.

    Example:
        classify_line_type("Valor do IVA 14%")  # LineType.TAX
    """
    folded = fold_for_matching(description)
    words = {word for word in folded.split() if not _NUMBER_OR_PERCENT.match(word)}
    if VAT_MARKER.search(folded) and words <= VAT_VOCABULARY:
        return LineType.TAX
    if DISCOUNT_MARKER.search(folded) and words <= DISCOUNT_VOCABULARY:
        return LineType.DISCOUNT
    return LineType.SERVICE
