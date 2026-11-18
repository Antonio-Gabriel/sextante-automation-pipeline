"""Versioned prompts (02-arquitectura.md §2.4). A prompt is code: changing it needs approval.

Each prompt file is read as written. Its version is recorded with every decision that
used it (REQ-AUD-003). Earlier versions stay in the repository, so a recorded version
can always be read back.
"""

from importlib.resources import files
from typing import Final

# item-choice-v1: approved 2026-11-18 (ticket 11). item-choice-v2: approved the same day;
# the candidate list moves to its own block so that it can be cached (CHG-0042).
ITEM_CHOICE_PROMPT_VERSION: Final = "item-choice-v2"
_PROMPT_FILES: Final = {
    "item-choice-v1": "item_choice_v1.txt",
    "item-choice-v2": "item_choice_v2.txt",
}


def item_choice_prompt(version: str = ITEM_CHOICE_PROMPT_VERSION) -> str:
    """The approved system prompt of the item choice, in the version asked for.

    Example:
        system = item_choice_prompt()  # the version in force, item-choice-v2

    Raises:
        KeyError: when no prompt has that version.
    """
    name = _PROMPT_FILES[version]
    return files(__package__).joinpath(name).read_text(encoding="utf-8").strip()
