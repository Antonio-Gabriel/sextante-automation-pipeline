"""Path parameters shared by every router (03-seguranca.md §9.1)."""

from typing import Annotated

from fastapi import Path

from sextante.platform.limits import IDENTIFIER_MAX_LENGTH, IDENTIFIER_PATTERN

# A server-generated identifier in a path: bounded and of a closed alphabet.
IdentifierPath = Annotated[str, Path(max_length=IDENTIFIER_MAX_LENGTH, pattern=IDENTIFIER_PATTERN)]
