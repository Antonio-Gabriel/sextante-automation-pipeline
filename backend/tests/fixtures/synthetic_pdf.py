"""SYNTHETIC PDF invoices in the layout of the sample model, written by hand (D-3.18).

Not real invoices. Each file says so in its metadata (Title and Producer). The layout
reproduces what the extractor must handle in the samples:

- the supplier name in a 16-point top band, long enough to run under "INVOICE / FACTURA";
- FROM and BILL TO blocks side by side;
- descriptions wrapped at a fixed character count, mid-word or on a space;
- values in the ``1,206.00`` format, and a total printed glued to its label.

No PDF library is needed: the file is a few objects with text placed at coordinates.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Final

PAGE_WIDTH: Final = 595.2756
PAGE_HEIGHT: Final = 841.8898
# pdfminer places a Helvetica glyph's top this far above the baseline, per point of size.
ASCENT: Final = 0.718
DESCRIPTION_WRAP: Final = 52
SYNTHETIC_TITLE: Final = "SYNTHETIC TEST INVOICE - not a real document"
# A grey area where a scanned image would be: shapes, no text.
SCANNED_SHAPE: Final = "0.8 g 40 400 515 400 re f"

# Helvetica advance widths (1/1000 em) of digits and separators, which right-aligned
# values are made of. Other characters get an average width, so right-aligned headings
# land a few points off; the extractor reads real positions, so that does not matter.
_WIDTHS: Final = {**dict.fromkeys("0123456789", 556), ",": 278, ".": 278, "%": 889, " ": 278}
_DEFAULT_WIDTH: Final = 556


@dataclass(frozen=True)
class PdfLine:
    """One table line as printed: the cells are already formatted text."""

    description: str
    quantity: str
    unit_price: str
    vat: str
    amount: str


@dataclass(frozen=True)
class PdfInvoice:
    """What a synthetic invoice prints. Empty strings are left out of the page."""

    supplier_name: str
    supplier_address: str
    supplier_nif: str
    number: str
    date: str
    currency: str
    bill_to: tuple[str, ...]
    lines: tuple[PdfLine, ...]
    summary: tuple[tuple[str, str], ...]
    notes: str
    glue_total: bool = False


@dataclass
class _Page:
    operations: list[str] = field(default_factory=list)

    def text(self, value: str, x: float, top: float, size: float, bold: bool = False) -> None:
        font = "F2" if bold else "F1"
        baseline = PAGE_HEIGHT - top - ASCENT * size
        self.operations.append(
            f"BT /{font} {size:g} Tf {x:.2f} {baseline:.2f} Td ({_escape(value)}) Tj ET"
        )

    def right(
        self, value: str, right_edge: float, top: float, size: float, bold: bool = False
    ) -> None:
        self.text(value, right_edge - _width(value, size), top, size, bold)


def model_invoice_pdf(invoice: PdfInvoice) -> bytes:
    """The invoice drawn in the layout of the sample model.

    Example:
        content = model_invoice_pdf(air_ticket_pdf())
    """
    page = _Page()
    _draw_header(page, invoice)
    _draw_parties(page, invoice)
    bottom = _draw_table(page, invoice)
    _draw_summary(page, invoice, bottom + 36)
    return _document([page.operations])


def with_scanned_page_pdf(invoice: PdfInvoice) -> bytes:
    """The invoice followed by a page with no text layer, like a partly scanned file.

    Example:
        with_scanned_page_pdf(air_ticket_pdf())
    """
    page = _Page()
    _draw_header(page, invoice)
    _draw_parties(page, invoice)
    _draw_summary(page, invoice, _draw_table(page, invoice) + 36)
    return _document([page.operations, [SCANNED_SHAPE]])


def scanned_pdf() -> bytes:
    """A page with an image-like shape and no text layer, like a scanned invoice.

    Example:
        scanned_pdf()
    """
    return _document([[SCANNED_SHAPE]])


def other_document_pdf() -> bytes:
    """A text PDF that is not an invoice of the model, like a customs assessment notice.

    Example:
        other_document_pdf()
    """
    page = _Page()
    page.text("SYNTHETIC CUSTOMS ASSESSMENT NOTICE", 200, 60, 12, bold=True)
    for row, text in enumerate(
        (
            "Customs office: Synthetic Office 01",
            "Declaration reference 2026 SYN000001",
            "Item taxes: Tax code 02K Imposto sobre a Importação 100.000",
            "Total assessed for the declaration 110.000",
            "Prazo limite para pagamento: 01/01/2026",
        )
    ):
        page.text(text, 40, 120 + 16 * row, 9)
    return _document([page.operations])


def _draw_header(page: _Page, invoice: PdfInvoice) -> None:
    page.text(invoice.supplier_name, 40, 32, 16, bold=True)
    page.right(f"INVOICE / FACTURA: {invoice.number}", 555, 30, 10)
    if invoice.date:
        page.right(f"Date: {invoice.date}", 555, 46, 10)


def _draw_parties(page: _Page, invoice: PdfInvoice) -> None:
    page.text("FROM / FORNECEDOR:", 40, 108, 9, bold=True)
    page.text("BILL TO / CLIENTE:", 300, 108, 9, bold=True)
    page.text(invoice.supplier_address, 40, 123, 9)
    if invoice.supplier_nif:
        page.text(f"NIF: {invoice.supplier_nif}", 40, 136, 9)
    for row, text in enumerate(invoice.bill_to):
        page.text(text, 300, 122 + 14 * row, 10 if row == 0 else 9, bold=row == 0)


def _draw_table(page: _Page, invoice: PdfInvoice) -> float:
    top = 196 + 14 * max(0, len(invoice.bill_to) - 3)
    page.text("Description / Descrição", 45, top, 9, bold=True)
    page.text("Qty", 340, top, 9, bold=True)
    page.text("Unit Price", 383, top, 9, bold=True)
    page.text("VAT", 457, top, 9, bold=True)
    page.right(f"Amount ({invoice.currency})", 550, top, 9, bold=True)
    row = top + 26
    for line in invoice.lines:
        chunks = _wrap(line.description)
        page.text(chunks[0], 45, row, 9)
        page.right(line.quantity, 355, row, 9)
        page.right(line.unit_price, 425, row, 9)
        page.right(line.vat, 475, row, 9)
        page.right(line.amount, 550, row, 9)
        for chunk in chunks[1:]:
            row += 12
            page.text(chunk, 45, row, 9)
        row += 16
    return row


def _draw_summary(page: _Page, invoice: PdfInvoice, top: float) -> None:
    for index, (label, amount) in enumerate(invoice.summary):
        is_total = index == len(invoice.summary) - 1
        size = 10 if is_total else 9
        if is_total and invoice.glue_total:
            page.right(f"{label}:{amount}", 525, top, size, bold=True)
        else:
            page.right(f"{label}:", 475, top, size, bold=is_total)
            page.right(amount, 529, top, size, bold=is_total)
        page.text(invoice.currency, 531, top, size, bold=is_total)
        top += 15
    if invoice.notes:
        page.text("Notes / Observações:", 40, top + 32, 8, bold=True)
        page.text(invoice.notes, 40, top + 44, 8)


def _wrap(description: str) -> list[str]:
    # Wrapped at a fixed character count, like the sample generator: a break can fall
    # mid-word, or on a space, which then opens the next row.
    return [
        description[start : start + DESCRIPTION_WRAP]
        for start in range(0, len(description), DESCRIPTION_WRAP)
    ] or [""]


def _width(text: str, size: float) -> float:
    return sum(_WIDTHS.get(character, _DEFAULT_WIDTH) for character in text) * size / 1000


def _escape(text: str) -> str:
    raw = text.encode("cp1252")
    escaped = raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
    return "".join(chr(byte) if byte < 128 else f"\\{byte:03o}" for byte in escaped)


def _document(pages: Sequence[Sequence[str]]) -> bytes:
    font = "<< /Type /Font /Subtype /Type1 /BaseFont /{} /Encoding /WinAnsiEncoding >>"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [{}] /Count {} >>",
        font.format("Helvetica"),
        font.format("Helvetica-Bold"),
        f"<< /Title ({SYNTHETIC_TITLE}) /Producer (sextante synthetic fixtures) >>",
    ]
    kids = []
    for operations in pages:
        stream = "\n".join(operations).encode("latin-1")
        objects.append(
            f"<< /Length {len(stream)} >>\nstream\n" + stream.decode("latin-1") + "\nendstream"
        )
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {len(objects)} 0 R >>"
        )
        kids.append(f"{len(objects)} 0 R")
    objects[1] = objects[1].format(" ".join(kids), len(kids))
    return _serialize(objects)


def _serialize(objects: list[str]) -> bytes:
    body = b"%PDF-1.4\n"
    offsets = []
    for number, content in enumerate(objects, start=1):
        offsets.append(len(body))
        body += f"{number} 0 obj\n".encode() + content.encode("latin-1") + b"\nendobj\n"
    xref = len(body)
    body += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    body += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
    trailer = f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R /Info 5 0 R >>\n"
    return body + trailer.encode() + f"startxref\n{xref}\n%%EOF\n".encode()


AMT_BILL_TO: Final = (
    "Advanced Maritime Transports - Transitarios Limitada",
    "Rua Sintética 1, Luanda, Angola",
    "NIF: 5419990000",
)


def air_ticket_pdf() -> PdfInvoice:
    """One line broken mid-word, and the total glued to its label (quirks of the samples).

    Example:
        model_invoice_pdf(air_ticket_pdf())
    """
    return PdfInvoice(
        supplier_name="Synthetic Airline Angola E.P.",
        supplier_address="Rua Sintética 123, Luanda, Angola",
        supplier_nif="5419990001",
        number="SYN-2026-001",
        date="2026-01-12",
        currency="AOA",
        bill_to=AMT_BILL_TO,
        lines=(
            PdfLine(
                "Passagem aérea Sintética - Rota Teste (Rotação equipa - Bilhete #SYN-0000001)",
                "1",
                "320,000.00",
                "0%",
                "320,000.00",
            ),
        ),
        summary=(("Subtotal", "320,000.00"), ("Tax / IVA", "0.00"), ("TOTAL", "320,000.00")),
        notes="Nota sintética: isento de IVA para efeitos de teste.",
        glue_total=True,
    )


def long_supplier_pdf() -> PdfInvoice:
    """A supplier name long enough to run under "INVOICE / FACTURA" (a quirk of the samples).

    Example:
        model_invoice_pdf(long_supplier_pdf())
    """
    return PdfInvoice(
        supplier_name="Escoltas Sintéticas & Trânsito de Teste Angola Lda",
        supplier_address="Av. Sintética, Luanda",
        supplier_nif="5419990002",
        number="DU-SYN001/26",
        date="2026-01-16",
        currency="AOA",
        bill_to=(
            "Petrolífera Sintética de Cabinda Lda",
            "Terminal Sintético, Cabinda, Angola",
            "NIF: 5419990003",
        ),
        lines=(
            PdfLine(
                "Escolta aduaneira de carga sintética (Porto Teste -> Base Teste)",
                "1",
                "95,000.00",
                "0%",
                "95,000.00",
            ),
        ),
        summary=(("Subtotal", "95,000.00"), ("Tax / IVA", "0.00"), ("TOTAL", "95,000.00")),
        notes="Ref. Processo Sintético #0001-SYN.",
    )


def care_of_pdf() -> PdfInvoice:
    """A "c/o" line, a break on a space, and USD values in the 1,206.00 format.

    Example:
        model_invoice_pdf(care_of_pdf())
    """
    return PdfInvoice(
        supplier_name="Synthetic Line Angola Limitada",
        supplier_address="Edifício Sintético, Luanda",
        supplier_nif="5419990004",
        number="AO-SYN0002",
        date="2026-01-14",
        currency="USD",
        bill_to=(
            "Operadora Sintética de Petróleo Angola",
            "c/o Advanced Maritime Transports",
            "Torre Sintética, Luanda, Angola",
            "NIF: 5419990005",
        ),
        lines=(
            PdfLine(
                "Sobrestadia sintética - Contentor SYNU0000001 (12d @ 100.50 USD/dia)",
                "12",
                "100.50",
                "0%",
                "1,206.00",
            ),
        ),
        summary=(("Subtotal", "1,206.00"), ("Tax / IVA", "0.00"), ("TOTAL", "1,206.00")),
        notes="Nota sintética: pagamento em USD.",
    )


def two_lines_with_vat_pdf() -> PdfInvoice:
    """Two lines, one with VAT, and an invoice number with a space.

    Example:
        model_invoice_pdf(two_lines_with_vat_pdf())
    """
    return PdfInvoice(
        supplier_name="Hotel Sintético Luanda",
        supplier_address="Rua Sintética, Luanda, Angola",
        supplier_nif="5419990006",
        number="FT 2026/0099",
        date="",
        currency="AOA",
        bill_to=AMT_BILL_TO,
        lines=(
            PdfLine(
                "Alojamento de 2 noites - Quarto Sintético (Visitante de teste)",
                "3",
                "130,000.00",
                "7%",
                "390,000.00",
            ),
            PdfLine("Serviço de restaurante sintético", "1", "65,000.00", "0%", "65,000.00"),
        ),
        summary=(("Subtotal", "455,000.00"), ("Tax / IVA", "27,300.00"), ("TOTAL", "482,300.00")),
        notes="",
    )
