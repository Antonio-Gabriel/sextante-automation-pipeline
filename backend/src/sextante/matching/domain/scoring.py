"""Lexical score of one line against one catalog item (REQ-MAP-004)."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LexicalScore:
    """Similarity of one line to one catalog item, and the item's rank for that line."""

    item_number: str
    score: float
    rank: int
