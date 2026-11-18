"""Classify each invoice line as service, tax or discount (REQ-ING-006, D-3.17, L-06)."""

import re
from enum import StrEnum
from typing import Final

from sextante.platform.text_normalization import fold_for_matching

# Tax means the supplier's VAT only, and only when the description starts with it: "Taxa
# de pilotagem" and customs duties are services, and "(isento de IVA)" inside a service
# description does not make it a tax line (D-3.17).
TAX_PATTERN: Final = re.compile(r"^(iva|vat|imposto sobre o valor acrescentado)\b")
DISCOUNT_PATTERN: Final = re.compile(r"^(desconto|discount|abatimento)\b")


class LineType(StrEnum):
    """Kind of an invoice line. Only services are coded (REQ-ING-006)."""

    SERVICE = "service"
    TAX = "tax"
    DISCOUNT = "discount"


def classify_line_type(description: str) -> LineType:
    """Return the line type; anything not recognised as tax or discount is a service.

    Example:
        classify_line_type("IVA 14%")  # LineType.TAX
    """
    folded = fold_for_matching(description)
    if TAX_PATTERN.match(folded):
        return LineType.TAX
    if DISCOUNT_PATTERN.match(folded):
        return LineType.DISCOUNT
    return LineType.SERVICE
