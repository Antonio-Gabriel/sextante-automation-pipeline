"""Read the entity denylist from its YAML file (REQ-ENT-003, L-04)."""

from pathlib import Path
from typing import Final

import yaml

from sextante.platform.errors import DomainError

DENYLIST_FORMAT_VERSION: Final = 1
DENYLIST_KINDS: Final = frozenset({"sister_company", "shipping_line", "client"})
MAX_DENYLIST_ENTRIES: Final = 1000
MAX_ENTITY_NAME_LENGTH: Final = 255


class DenylistFileError(DomainError):
    """The denylist file is missing or does not follow its documented structure."""

    user_message_key = "errors.internal"


def read_entity_denylist(path: Path) -> frozenset[str]:
    """Return the denylisted names, as written. safe_load never builds Python objects.

    Example:
        read_entity_denylist(Path("config/entity_denylist.yaml"))  # frozenset()

    Raises:
        DenylistFileError: naming what is wrong and the expected structure.
    """
    if not path.is_file():
        raise DenylistFileError(f"Denylist file {path.name!r} does not exist.")
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or document.get("version") != DENYLIST_FORMAT_VERSION:
        raise DenylistFileError(
            f"Denylist file {path.name!r} has no 'version: {DENYLIST_FORMAT_VERSION}'. "
            "Expected a mapping with 'version' and 'entities'."
        )
    return frozenset(_entry_name(entry, index) for index, entry in enumerate(_entries(document)))


def _entries(document: dict[str, object]) -> list[object]:
    entries = document.get("entities")
    if not isinstance(entries, list) or len(entries) > MAX_DENYLIST_ENTRIES:
        raise DenylistFileError(
            f"Denylist 'entities' must be a list of at most {MAX_DENYLIST_ENTRIES} entries."
        )
    return entries


def _entry_name(entry: object, index: int) -> str:
    if not isinstance(entry, dict):
        raise DenylistFileError(f"Denylist entry {index} is not a mapping with 'name' and 'kind'.")
    name, kind = entry.get("name"), entry.get("kind")
    if not isinstance(name, str) or not name.strip() or len(name) > MAX_ENTITY_NAME_LENGTH:
        raise DenylistFileError(
            f"Denylist entry {index} has no valid 'name'. Expected 1 to "
            f"{MAX_ENTITY_NAME_LENGTH} characters."
        )
    if kind not in DENYLIST_KINDS:
        raise DenylistFileError(
            f"Denylist entry {index} has kind {kind!r}. Expected one of {sorted(DENYLIST_KINDS)}."
        )
    return name
