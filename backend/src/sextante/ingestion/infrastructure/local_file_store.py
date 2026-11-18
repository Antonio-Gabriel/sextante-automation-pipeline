"""Uploaded files on local disk, under server-generated names (SEC-16)."""

import re
from pathlib import Path
from typing import Final

# Storage names are generated from the digest; anything else is refused, so that no
# client-supplied text ever reaches a filesystem path.
STORAGE_NAME_PATTERN: Final = re.compile(r"^[0-9a-f]{64}\.(pdf|xlsx)$")


class LocalInvoiceFileStore:
    """Implements InvoiceFileStore on a local directory.

    Example:
        store = LocalInvoiceFileStore(Path("uploads"))
    """

    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def save(self, storage_name: str, content: bytes) -> None:
        """Write the content. Same digest, same name: rewriting is harmless.

        Example:
            store.save(f"{digest}.pdf", content)
        """
        self._path_for(storage_name).write_bytes(content)

    def read(self, storage_name: str) -> bytes:
        """Return the stored content.

        Example:
            store.read(f"{digest}.pdf")
        """
        return self._path_for(storage_name).read_bytes()

    def _path_for(self, storage_name: str) -> Path:
        if not STORAGE_NAME_PATTERN.fullmatch(storage_name):
            raise ValueError(
                f"Storage name {storage_name!r} is not server-generated. "
                "Expected '<sha256>.pdf' or '<sha256>.xlsx'."
            )
        return self._root / storage_name
