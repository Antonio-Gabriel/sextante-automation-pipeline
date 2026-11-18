"""Size limits shared across modules (03-seguranca.md §9.1). Every limit is Final."""

from typing import Final

# The model receives the whole target sheet (D-3.16), so this caps the size of one
# catalog sheet rather than a per-line candidate count (03-seguranca.md §9.1).
MAX_SHEET_ITEMS: Final = 100

# 03-seguranca.md §9.1.
MAX_UPLOAD_BYTES: Final = 25 * 1024 * 1024
MAX_FILES_PER_UPLOAD: Final = 50
MAX_FILE_NAME_LENGTH: Final = 255
MAX_LINES_PER_INVOICE: Final = 500
MAX_PAGE_SIZE: Final = 100
MAX_RATIONALE_LENGTH: Final = 500
IDENTIFIER_MAX_LENGTH: Final = 64
