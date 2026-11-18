"""Ticket 12: native PDF extraction in the sample model, on SYNTHETIC replicas (D-3.6).

Tested at the InvoiceExtractor port: what the extractor returns for a file is what the
rest of the system stores and codes.
"""

import dataclasses
import logging
from decimal import Decimal

import pytest

from sextante.ingestion.domain.model import (
    BilledEntityBlock,
    ExtractedInvoice,
    ExtractionRejection,
    FileFormat,
    RejectionReason,
    SummaryRow,
)
from sextante.ingestion.infrastructure.pdf_invoice_extractor import PdfInvoiceExtractor
from tests.fixtures.synthetic_pdf import (
    PdfInvoice,
    air_ticket_pdf,
    care_of_pdf,
    long_supplier_pdf,
    model_invoice_pdf,
    other_document_pdf,
    scanned_pdf,
    two_lines_with_vat_pdf,
    with_scanned_page_pdf,
)

MIN_CHARS_PER_PAGE = 100
EXTRACTOR_LOGGER = "sextante.ingestion.infrastructure.pdf_invoice_extractor"


def _extract(invoice: PdfInvoice) -> ExtractedInvoice:
    result = PdfInvoiceExtractor(MIN_CHARS_PER_PAGE).extract(
        model_invoice_pdf(invoice), FileFormat.PDF
    )
    assert isinstance(result, ExtractedInvoice), result
    return result


@pytest.mark.requirement("REQ-ING-003", "D-3.6")
def test_the_supplier_name_is_read_from_the_top_band_alone() -> None:
    """A long name runs under "INVOICE / FACTURA" and still comes out whole and alone."""
    extraction = _extract(long_supplier_pdf())

    assert extraction.supplier.name == "Escoltas Sintéticas & Trânsito de Teste Angola Lda"
    assert extraction.invoice_number == "DU-SYN001/26"


@pytest.mark.requirement("REQ-ING-003", "REQ-ING-005")
def test_from_and_bill_to_are_separated_by_position() -> None:
    """Each side keeps its own NIF; the billed entity is the first line of BILL TO."""
    extraction = _extract(air_ticket_pdf())

    assert extraction.supplier.nif == "5419990001"
    assert extraction.billed_entities == (
        BilledEntityBlock(
            name="Advanced Maritime Transports - Transitarios Limitada",
            nif="5419990000",
            care_of=(),
            address_lines=("Rua Sintética 1, Luanda, Angola",),
        ),
    )


@pytest.mark.requirement("REQ-ING-005", "D-3.15")
def test_a_care_of_line_is_kept_apart_from_the_billed_entity() -> None:
    """ "c/o AMT" never becomes the billed entity."""
    [block] = _extract(care_of_pdf()).billed_entities

    assert (block.name, block.care_of, block.nif) == (
        "Operadora Sintética de Petróleo Angola",
        ("Advanced Maritime Transports",),
        "5419990005",
    )


@pytest.mark.requirement("REQ-ING-003")
def test_number_date_and_currency_come_from_the_header_and_the_amount_column() -> None:
    """A number may contain a space; the currency is the one of the amount heading."""
    extraction = _extract(two_lines_with_vat_pdf())
    usd = _extract(care_of_pdf())

    assert (extraction.invoice_number, extraction.currency) == ("FT 2026/0099", "AOA")
    assert (usd.invoice_date, usd.currency) == ("2026-01-14", "USD")


@pytest.mark.requirement("REQ-ING-004")
def test_a_continuation_row_joins_without_space_mid_word_and_with_space_on_a_space() -> None:
    """ "Tic" + "ket" gives "Ticket"; "@" + " 100.50" keeps its space."""
    [ticket] = _extract(air_ticket_pdf()).lines
    [demurrage] = _extract(care_of_pdf()).lines

    assert ticket.description == (
        "Passagem aérea Sintética - Rota Teste (Rotação equipa - Bilhete #SYN-0000001)"
    )
    assert demurrage.description == (
        "Sobrestadia sintética - Contentor SYNU0000001 (12d @ 100.50 USD/dia)"
    )


@pytest.mark.requirement("REQ-ING-004")
def test_values_are_read_in_the_1_450_00_format() -> None:
    """Quantity, unit price, VAT rate and amount, each in its own column."""
    [demurrage] = _extract(care_of_pdf()).lines
    first, second = _extract(two_lines_with_vat_pdf()).lines

    assert (demurrage.quantity, demurrage.unit_price, demurrage.amount) == (
        Decimal("12"),
        Decimal("100.50"),
        Decimal("1206.00"),
    )
    assert (first.position, first.vat_rate, first.amount) == (1, Decimal("7"), Decimal("390000.00"))
    assert (second.position, second.description) == (2, "Serviço de restaurante sintético")


@pytest.mark.requirement("REQ-ING-006", "D-3.17")
def test_summary_rows_and_notes_are_kept_apart_from_the_lines() -> None:
    """Subtotal, VAT and total are summary rows, even with the total glued to its label."""
    extraction = _extract(air_ticket_pdf())

    assert extraction.summary_rows == (
        SummaryRow("Subtotal", Decimal("320000.00")),
        SummaryRow("Tax / IVA", Decimal("0.00")),
        SummaryRow("TOTAL", Decimal("320000.00")),
    )
    assert extraction.notes == "Nota sintética: isento de IVA para efeitos de teste."
    assert len(extraction.lines) == 1


@pytest.mark.requirement("REQ-ING-003", "SEC-15")
def test_a_missing_field_stays_empty_and_is_logged_by_name_only(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """No date printed: the date is None, never guessed, and the log names the field only."""
    # The application's logging setup stops propagation at "sextante", so the capture
    # handler is attached to the extractor's own logger.
    extractor_logger = logging.getLogger(EXTRACTOR_LOGGER)
    extractor_logger.addHandler(caplog.handler)
    caplog.set_level(logging.INFO, logger=EXTRACTOR_LOGGER)
    try:
        extraction = _extract(two_lines_with_vat_pdf())
    finally:
        extractor_logger.removeHandler(caplog.handler)

    # Whether or not "sextante" propagates, the same record may reach the capture twice.
    [record] = {
        id(r): r for r in caplog.records if r.message == "extraction_fields_missing"
    }.values()
    assert extraction.invoice_date is None
    assert record.missing_fields == ["invoice_date"]  # type: ignore[attr-defined]
    assert "Hotel" not in caplog.text


@pytest.mark.requirement("REQ-ING-002", "L-01")
def test_a_pdf_without_enough_text_per_page_is_refused_as_scanned() -> None:
    """No text layer, or less than the configured minimum, is pdf_without_text_layer."""
    extractor = PdfInvoiceExtractor(MIN_CHARS_PER_PAGE)
    sparse = PdfInvoiceExtractor(min_chars_per_page=10_000)

    assert extractor.extract(scanned_pdf(), FileFormat.PDF) == ExtractionRejection(
        RejectionReason.PDF_WITHOUT_TEXT_LAYER
    )
    assert sparse.extract(model_invoice_pdf(air_ticket_pdf()), FileFormat.PDF) == (
        ExtractionRejection(RejectionReason.PDF_WITHOUT_TEXT_LAYER)
    )


@pytest.mark.requirement("REQ-ING-002", "L-01")
def test_one_scanned_page_among_native_ones_refuses_the_pdf() -> None:
    """The minimum holds for every page, not on average over the file."""
    content = with_scanned_page_pdf(air_ticket_pdf())

    result = PdfInvoiceExtractor(MIN_CHARS_PER_PAGE).extract(content, FileFormat.PDF)

    assert result == ExtractionRejection(RejectionReason.PDF_WITHOUT_TEXT_LAYER)


@pytest.mark.requirement("REQ-ING-009", "L-14")
def test_a_document_without_the_model_structure_is_refused() -> None:
    """A customs notice has text but no FROM, BILL TO or table: unsupported_document_type."""
    result = PdfInvoiceExtractor(MIN_CHARS_PER_PAGE).extract(other_document_pdf(), FileFormat.PDF)

    assert result == ExtractionRejection(RejectionReason.UNSUPPORTED_DOCUMENT_TYPE)


@pytest.mark.requirement("REQ-ING-009", "SEC-16")
def test_a_file_that_is_not_a_readable_pdf_is_refused_not_failed() -> None:
    """A truncated PDF is refused: reading it again would give the same result."""
    truncated = model_invoice_pdf(air_ticket_pdf())[:200]

    result = PdfInvoiceExtractor(MIN_CHARS_PER_PAGE).extract(truncated, FileFormat.PDF)

    assert result == ExtractionRejection(RejectionReason.UNSUPPORTED_DOCUMENT_TYPE)


@pytest.mark.requirement("D-3.6", "L-01")
def test_xlsx_extraction_is_not_available_in_this_version() -> None:
    """No XLSX sample exists, so no XLSX reader: refused with its own reason."""
    result = PdfInvoiceExtractor(MIN_CHARS_PER_PAGE).extract(b"PK\x03\x04", FileFormat.XLSX)

    assert result == ExtractionRejection(RejectionReason.EXTRACTOR_NOT_CONFIGURED)


@pytest.mark.requirement("REQ-ING-003")
def test_a_line_without_values_keeps_them_empty() -> None:
    """Absent cells stay None: the extractor never fills a value it did not read."""
    line = dataclasses.replace(air_ticket_pdf().lines[0], unit_price="", vat="")
    invoice = dataclasses.replace(air_ticket_pdf(), lines=(line,))

    [extracted] = _extract(invoice).lines

    assert (extracted.unit_price, extracted.vat_rate) == (None, None)
    assert extracted.amount == Decimal("320000.00")
