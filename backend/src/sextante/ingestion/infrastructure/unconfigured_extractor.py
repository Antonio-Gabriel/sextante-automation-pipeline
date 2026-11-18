"""Placeholder extractor until native PDF extraction lands (ticket 12)."""

from sextante.ingestion.domain.model import (
    ExtractedInvoice,
    ExtractionRejection,
    FileFormat,
    RejectionReason,
)


class UnconfiguredInvoiceExtractor:
    """Refuses every document with an explicit reason, never with an invented result.

    Example:
        UnconfiguredInvoiceExtractor().extract(content, FileFormat.PDF)  # rejection
    """

    def extract(
        self, content: bytes, file_format: FileFormat
    ) -> ExtractedInvoice | ExtractionRejection:
        """Refuse the document: no extractor is configured in this build."""
        return ExtractionRejection(reason=RejectionReason.EXTRACTOR_NOT_CONFIGURED)
