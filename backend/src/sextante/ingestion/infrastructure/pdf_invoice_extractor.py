"""Native PDF extraction for invoices in the sample model (D-3.6, REQ-ING-002/003, L-01).

A scanned PDF has no text layer and is refused with ``pdf_without_text_layer``; a PDF
that is not an invoice of the model, such as a customs assessment notice, is refused
with ``unsupported_document_type`` (L-14). Neither is ever coded. XLSX extraction is not
implemented in this version (D-3.6): an XLSX upload is refused as
``unsupported_document_type``, as REQ-ING-001 sends it to REQ-ING-009.
"""

import io
import logging
from typing import Final

import pdfplumber
from pdfminer.pdfparser import PDFSyntaxError
from pdfplumber.page import Page
from pdfplumber.utils.exceptions import PdfminerException

from sextante.ingestion.domain.model import (
    ExtractedInvoice,
    ExtractionRejection,
    FileFormat,
    RejectionReason,
    missing_fields,
)
from sextante.ingestion.infrastructure.model_invoice_layout import Glyph, Word, read_model_invoice
from sextante.platform.limits import MAX_PDF_PAGES

logger = logging.getLogger(__name__)

# Pages are stacked one under the other, so a table that runs over a page break keeps
# its rows in order.
PAGE_GAP: Final = 50.0


class PdfInvoiceExtractor:
    """InvoiceExtractor for PDF invoices with a text layer, in the layout of the samples.

    Example:
        PdfInvoiceExtractor(min_chars_per_page=100).extract(content, FileFormat.PDF)
    """

    def __init__(self, min_chars_per_page: int) -> None:
        self._min_chars_per_page = min_chars_per_page

    def extract(
        self, content: bytes, file_format: FileFormat
    ) -> ExtractedInvoice | ExtractionRejection:
        """Extract the invoice, or refuse it with a reason. Never guesses a field.

        Example:
            extractor.extract(pdf_bytes, FileFormat.PDF).invoice_number
        """
        if file_format is not FileFormat.PDF:
            return ExtractionRejection(RejectionReason.UNSUPPORTED_DOCUMENT_TYPE)
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                return self._extract_pages(pdf.pages)
        except (PDFSyntaxError, PdfminerException) as error:
            # Memory ran out while pdfminer read the file: pdfplumber wraps it, and the
            # isolated extractor must see it as the limit it is (SEC-16).
            if _out_of_memory(error):
                raise MemoryError("PDF extraction ran out of memory.") from error
            # The file starts like a PDF but cannot be read as one: refused, not failed,
            # because retrying would read it the same way.
            logger.warning("pdf_unreadable", extra={"error_type": type(error).__name__})
            return ExtractionRejection(RejectionReason.UNSUPPORTED_DOCUMENT_TYPE)

    def _extract_pages(self, pages: list[Page]) -> ExtractedInvoice | ExtractionRejection:
        # Counting pages reads only the page tree; no content stream is decoded before
        # the count is known to be within the limit.
        if not pages or len(pages) > MAX_PDF_PAGES:
            return ExtractionRejection(RejectionReason.UNSUPPORTED_DOCUMENT_TYPE)
        # Each page must have enough text: a scanned page among native ones is not read
        # as an empty page of a valid invoice (REQ-ING-002).
        if any(len(page.chars) < self._min_chars_per_page for page in pages):
            return ExtractionRejection(RejectionReason.PDF_WITHOUT_TEXT_LAYER)
        words, glyphs = _stacked_text(pages)
        invoice = read_model_invoice(words, glyphs)
        if invoice is None:
            return ExtractionRejection(RejectionReason.UNSUPPORTED_DOCUMENT_TYPE)
        missing = missing_fields(invoice)
        if missing:
            logger.info("extraction_fields_missing", extra={"missing_fields": list(missing)})
        return invoice


def _out_of_memory(error: BaseException) -> bool:
    cause: BaseException | None = error
    while cause is not None:
        if isinstance(cause, MemoryError) or any(isinstance(a, MemoryError) for a in cause.args):
            return True
        cause = cause.__cause__ or cause.__context__
    return False


def _stacked_text(pages: list[Page]) -> tuple[list[Word], list[Glyph]]:
    words: list[Word] = []
    glyphs: list[Glyph] = []
    offset = 0.0
    for page in pages:
        for word in page.extract_words(extra_attrs=["size"]):
            top = float(word["top"]) + offset
            words.append(
                Word(
                    str(word["text"]),
                    float(word["x0"]),
                    float(word["x1"]),
                    top,
                    float(word["size"]),
                )
            )
        glyphs += [
            Glyph(str(c["text"]), float(c["x0"]), float(c["top"]) + offset) for c in page.chars
        ]
        offset += float(page.height) + PAGE_GAP
    return words, glyphs
