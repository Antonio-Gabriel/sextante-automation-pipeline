"""Versioned prompts (02-arquitectura.md §2.4). A prompt is code: changing it needs approval.

Each prompt file is read as written. Its version is recorded with every decision that
used it (REQ-AUD-003).
"""

from importlib.resources import files
from typing import Final

ITEM_CHOICE_PROMPT_VERSION: Final = "item-choice-v1"


def item_choice_prompt() -> str:
    """The approved system prompt of the item choice, version item-choice-v1.

    Approved by the project owner on 2026-11-18 (ticket 11).

    Example:
        system = item_choice_prompt()
    """
    return files(__package__).joinpath("item_choice_v1.txt").read_text(encoding="utf-8").strip()
