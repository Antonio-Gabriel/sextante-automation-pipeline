"""Ports of the ingestion module (02-arquitectura.md §2.3)."""

from typing import Protocol

from sextante.ingestion.domain.model import ExtractedInvoice, ExtractionRejection, FileFormat


class InvoiceExtractor(Protocol):
    """Port: read one invoice file into an ExtractedInvoice, or refuse it with a reason."""

    def extract(
        self, content: bytes, file_format: FileFormat
    ) -> ExtractedInvoice | ExtractionRejection:
        """Extract the invoice. Never guesses a field it did not find (REQ-ING-003)."""
        ...


class InvoiceFileStore(Protocol):
    """Port: keep uploaded files under server-generated names (SEC-16)."""

    def save(self, storage_name: str, content: bytes) -> None:
        """Write the content under the given server-generated name."""
        ...

    def read(self, storage_name: str) -> bytes:
        """Return the content stored under the name."""
        ...
