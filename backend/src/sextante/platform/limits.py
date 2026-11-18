"""Size limits shared across modules (03-seguranca.md §9.1). Every limit is Final."""

from typing import Final

# The model receives the whole target sheet (D-3.16), so this caps the size of one
# catalog sheet rather than a per-line candidate count (03-seguranca.md §9.1).
MAX_SHEET_ITEMS: Final = 100
