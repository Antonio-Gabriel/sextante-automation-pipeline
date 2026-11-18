"""In-memory InvoiceExtractor for tests. Returns declared extractions by file content."""

from collections.abc import Iterable

from sextante.ingestion.contracts import ExtractedInvoice, ExtractionRejection, FileFormat
from tests.fixtures.synthetic_invoices import SyntheticInvoice


class FakeInvoiceExtractor:
    """Returns the extraction declared for each synthetic invoice, and records calls.

    Example:
        extractor = FakeInvoiceExtractor([taag_air_ticket_to_amt()])
    """

    def __init__(self, invoices: Iterable[SyntheticInvoice]) -> None:
        self._extractions = {invoice.content: invoice.extraction for invoice in invoices}
        self.calls: list[bytes] = []

    def extract(
        self, content: bytes, file_format: FileFormat
    ) -> ExtractedInvoice | ExtractionRejection:
        """Return the declared extraction for these bytes."""
        self.calls.append(content)
        return self._extractions[content]
