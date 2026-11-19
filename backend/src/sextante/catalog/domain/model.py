"""Catalog value objects. Pure: no I/O (02-arquitectura.md §2.3)."""

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from sextante.platform.language import Language

# The item number format of 03-seguranca.md SEC-09.2. It also refuses a code with
# surrounding spaces, which would break the exact-value rule R1 without being visible.
ITEM_NUMBER_PATTERN: Final = re.compile(r"^[A-Z0-9][A-Z0-9._/-]{0,31}$")
SHA256_HEX_PATTERN: Final = re.compile(r"^[0-9a-f]{64}$")


class TargetSheet(StrEnum):
    """The two catalog sheets. Routing picks exactly one (R2, REQ-MAP-001)."""

    OUTLAYS = "OUTLAYS"
    OUTLAYSP = "OUTLAYSP"


@dataclass(frozen=True, slots=True)
class ItemNumber:
    """The exact value of column No. of the catalog (R1, REQ-MAP-003).

    Raises ValueError when the value does not match ITEM_NUMBER_PATTERN.

    Example:
        ItemNumber("O00999")
    """

    value: str

    def __post_init__(self) -> None:
        if not ITEM_NUMBER_PATTERN.fullmatch(self.value):
            raise ValueError(
                f"Item number {self.value!r} does not match {ITEM_NUMBER_PATTERN.pattern}, "
                "for example 'O00004'."
            )

    def __str__(self) -> str:
        return self.value


FALLBACK_ITEM_NUMBER: Final = ItemNumber("O00999")


@dataclass(frozen=True, slots=True)
class CatalogDigest:
    """SHA-256 of the catalog file, recorded on every encoded line (D-3.9, REQ-MAP-011).

    Example:
        CatalogDigest(hashlib.sha256(content).hexdigest())
    """

    hex_value: str

    def __post_init__(self) -> None:
        if not SHA256_HEX_PATTERN.fullmatch(self.hex_value):
            raise ValueError(
                f"Catalog digest {self.hex_value!r} is not a SHA-256. "
                "Expected 64 lowercase hexadecimal characters."
            )

    def __str__(self) -> str:
        return self.hex_value


@dataclass(frozen=True, slots=True)
class CatalogItem:
    """One catalog row: presentation values for output, comparison values for scoring.

    The catalog is never corrected in code (L-05): presentation values keep the source
    text, trimmed only at the ends.

    Example:
        catalog_item.description_pt  # "Bilhete Avião", as exported
    """

    item_number: ItemNumber
    sheet: TargetSheet
    description_pt: str
    description_en: str
    comparison_pt: str
    comparison_en: str


@dataclass(frozen=True, slots=True)
class Catalog:
    """The loaded catalog, kept in memory for the life of the process (NFR-PRF-003).

    Example:
        catalog.items_of(TargetSheet.OUTLAYS)
    """

    digest: CatalogDigest
    outlays: tuple[CatalogItem, ...]
    outlaysp: tuple[CatalogItem, ...]

    def find(self, item_number: ItemNumber) -> CatalogItem | None:
        """Return the item with this number, in either sheet, or None.

        Example:
            catalog.find(FALLBACK_ITEM_NUMBER)  # the O00999 item of OUTLAYSP
        """
        return next((c for c in self.outlays + self.outlaysp if c.item_number == item_number), None)

    def description_in(
        self, item_number: str | None, language: Language, recorded: str | None
    ) -> str | None:
        """The description of an item to show in a language.

        Portuguese shows the description recorded with the decision. English shows the
        item's English description, or its Portuguese one when the catalog has none; an
        item no longer in the catalog keeps the recorded text.

        Example:
            catalog.description_in("O00004", Language.EN, "Bilhete Avião")  # "Air ticket"
        """
        if language is Language.PT or item_number is None:
            return recorded
        try:
            item = self.find(ItemNumber(item_number))
        except ValueError:
            return recorded
        if item is None:
            return recorded
        return item.description_en or item.description_pt

    def items_of(self, sheet: TargetSheet) -> tuple[CatalogItem, ...]:
        """Return the items of one sheet, in catalog order. Sheets never mix (REQ-MAP-002).

        Example:
            catalog.items_of(TargetSheet.OUTLAYSP)
        """
        return self.outlays if sheet is TargetSheet.OUTLAYS else self.outlaysp
