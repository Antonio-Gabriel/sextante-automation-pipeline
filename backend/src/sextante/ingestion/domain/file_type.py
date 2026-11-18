"""File type from the first bytes of the content (REQ-ING-001, SEC-16 step 4)."""

from typing import Final

from sextante.ingestion.domain.model import FileFormat

PDF_SIGNATURE: Final = b"%PDF-"
# XLSX is a ZIP archive; its structure is checked when the extractor opens it.
ZIP_SIGNATURE: Final = b"PK\x03\x04"


def detect_file_format(head: bytes) -> FileFormat | None:
    """Return the format the content really has, or None when it is not accepted.

    The extension and the declared Content-Type are both chosen by the uploader, so
    neither is consulted.

    Example:
        detect_file_format(b"%PDF-1.7 ...")  # FileFormat.PDF
    """
    if head.startswith(PDF_SIGNATURE):
        return FileFormat.PDF
    if head.startswith(ZIP_SIGNATURE):
        return FileFormat.XLSX
    return None
