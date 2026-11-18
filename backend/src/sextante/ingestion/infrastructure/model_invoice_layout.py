"""Read the words of a PDF in the sample model into an ExtractedInvoice (D-3.6, REQ-ING-003).

The layout is found by its labels and by word coordinates, never by line order alone:
the supplier name sits in a larger font in the top band, FROM and BILL TO are side by
side, and table cells are right-aligned under their headings. A field that is not found
stays None; nothing is inferred.
"""

import dataclasses
import re
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Final

from sextante.ingestion.domain.model import (
    BilledEntityBlock,
    ExtractedInvoice,
    ExtractedLine,
    PartyIdentity,
    SummaryRow,
)

ROW_TOLERANCE: Final = 2.5
# The supplier band is set in a clearly larger font than the "INVOICE / FACTURA" label.
BAND_FONT_MARGIN: Final = 2.0
CARE_OF_PREFIXES: Final = ("c/o ", "a/c ")
AMOUNT_PATTERN: Final = re.compile(r"^-?\d{1,3}(?:,\d{3})*(?:\.\d+)?$|^-?\d+(?:\.\d+)?$")
SUMMARY_PATTERN: Final = re.compile(
    r"^(?P<label>[^:]+):\s*(?P<amount>-?[\d,]+\.\d{2})\s*(?:[A-Z]{3})?$"
)
CURRENCY_PATTERN: Final = re.compile(r"\(([A-Z]{3})\)")


@dataclass(frozen=True, slots=True)
class Word:
    """A word of the text layer, with its box and font size, in page-stacked coordinates."""

    text: str
    x0: float
    x1: float
    top: float
    size: float


@dataclass(frozen=True, slots=True)
class Glyph:
    """One character of the text layer, spaces included, which words drop."""

    text: str
    x0: float
    top: float


@dataclass(frozen=True, slots=True)
class _Row:
    top: float
    words: tuple[Word, ...]

    @property
    def text(self) -> str:
        return " ".join(word.text for word in self.words)

    def word_after(self, label: str) -> str | None:
        # The value printed to the right of a label, or glued to it ("FACTURA:SYN-1").
        for index, word in enumerate(self.words):
            if word.text.startswith(label):
                glued = word.text[len(label) :]
                following = self.words[index + 1].text if index + 1 < len(self.words) else None
                return glued or following
        return None


@dataclass(frozen=True, slots=True)
class _Columns:
    description_limit: float
    quantity: float
    unit_price: float
    vat: float
    amount: float


@dataclass(frozen=True, slots=True)
class _Anchors:
    invoice_row: _Row
    parties_row: _Row
    bill_to_x: float
    table_row: _Row
    columns: _Columns


def read_model_invoice(words: Sequence[Word], glyphs: Sequence[Glyph]) -> ExtractedInvoice | None:
    """Return the invoice, or None when the words lack the structure of the model.

    Example:
        read_model_invoice(words, glyphs).invoice_number  # "SYN-2026-001"
    """
    rows = _rows(words)
    anchors = _anchors(rows)
    if anchors is None:
        return None
    summary_start = _summary_start(rows, anchors.table_row)
    notes_row = _first(rows, lambda row: row.top > anchors.table_row.top and _is_notes(row))
    return ExtractedInvoice(
        supplier=PartyIdentity(_supplier_name(rows, anchors), _supplier_nif(rows, anchors)),
        invoice_number=_invoice_number(anchors.invoice_row),
        invoice_date=_date(rows, anchors),
        currency=_currency(anchors.table_row),
        billed_entities=_billed_blocks(rows, anchors),
        lines=_lines(rows, glyphs, anchors, summary_start),
        summary_rows=_summary(rows, summary_start, notes_row),
        notes=_notes(rows, notes_row),
    )


def _rows(words: Iterable[Word]) -> list[_Row]:
    rows: list[list[Word]] = []
    for word in sorted(words, key=lambda w: (w.top, w.x0)):
        if rows and word.top - rows[-1][0].top <= ROW_TOLERANCE:
            rows[-1].append(word)
        else:
            rows.append([word])
    return [_Row(row[0].top, tuple(sorted(row, key=lambda w: w.x0))) for row in rows]


def _anchors(rows: list[_Row]) -> _Anchors | None:
    invoice_row = _first(rows, lambda row: any(w.text.startswith("FACTURA:") for w in row.words))
    parties_row = _first(rows, lambda row: "FROM" in _texts(row) and "BILL" in _texts(row))
    table_row = _first(rows, lambda row: {"Description", "Qty", "VAT"} <= set(_texts(row)))
    if invoice_row is None or parties_row is None or table_row is None:
        return None
    bill = next(word for word in parties_row.words if word.text == "BILL")
    columns = _columns(table_row)
    if columns is None:
        return None
    return _Anchors(invoice_row, parties_row, bill.x0, table_row, columns)


def _columns(table_row: _Row) -> _Columns | None:
    # Cells are right-aligned, so each column is known by the right edge of its heading.
    by_text = {word.text: word for word in table_row.words}
    if not {"Qty", "Price", "VAT"} <= set(by_text):
        return None
    return _Columns(
        description_limit=by_text["Qty"].x0 - 2,
        quantity=by_text["Qty"].x1,
        unit_price=by_text["Price"].x1,
        vat=by_text["VAT"].x1,
        amount=table_row.words[-1].x1,
    )


def _invoice_label(invoice_row: _Row) -> Word:
    return next(w for w in invoice_row.words if w.text.startswith("FACTURA:"))


def _invoice_number(invoice_row: _Row) -> str | None:
    # The number may hold a space ("FT 2026/0001"). The supplier band shares the row's
    # height but not its font size, so only words in the label's size are taken.
    label = _invoice_label(invoice_row)
    glued = label.text.removeprefix("FACTURA:")
    after = [
        w.text
        for w in invoice_row.words
        if w.x0 > label.x0 and abs(w.size - label.size) < BAND_FONT_MARGIN
    ]
    number = " ".join(([glued] if glued else []) + after)
    return number or None


def _supplier_name(rows: list[_Row], anchors: _Anchors) -> str | None:
    band = [w for row in rows if row.top < anchors.parties_row.top for w in row.words]
    label_size = _invoice_label(anchors.invoice_row).size
    largest = max((w.size for w in band), default=0.0)
    if largest < label_size + BAND_FONT_MARGIN:
        return None
    # Only the band's large words: the label row they overlap is in a smaller font.
    return " ".join(w.text for w in sorted(band, key=lambda w: w.x0) if w.size == largest)


def _supplier_nif(rows: list[_Row], anchors: _Anchors) -> str | None:
    for row in _between(rows, anchors.parties_row.top, anchors.table_row.top):
        left = _Row(row.top, tuple(w for w in row.words if w.x1 < anchors.bill_to_x))
        if left.words and left.words[0].text == "NIF:":
            return left.word_after("NIF:")
    return None


def _date(rows: list[_Row], anchors: _Anchors) -> str | None:
    header = _between(rows, -1.0, anchors.parties_row.top)
    return next((row.word_after("Date:") for row in header if "Date:" in _texts(row)), None)


def _currency(table_row: _Row) -> str | None:
    match = CURRENCY_PATTERN.search(table_row.text)
    return match.group(1) if match else None


def _billed_blocks(rows: list[_Row], anchors: _Anchors) -> tuple[BilledEntityBlock, ...]:
    region = _between(rows, anchors.parties_row.top, anchors.table_row.top)
    texts = [" ".join(w.text for w in row.words if w.x0 >= anchors.bill_to_x - 1) for row in region]
    texts = [text for text in texts if text]
    if not texts:
        return ()
    name, rest = texts[0], texts[1:]
    nif = next(
        (text.removeprefix("NIF:").strip() for text in rest if text.startswith("NIF:")), None
    )
    care_of = tuple(text[4:].strip() for text in rest if text.lower().startswith(CARE_OF_PREFIXES))
    address = tuple(
        text
        for text in rest
        if not text.startswith("NIF:") and not text.lower().startswith(CARE_OF_PREFIXES)
    )
    return (BilledEntityBlock(name=name, nif=nif or None, care_of=care_of, address_lines=address),)


def _lines(
    rows: list[_Row], glyphs: Sequence[Glyph], anchors: _Anchors, summary_start: float
) -> tuple[ExtractedLine, ...]:
    columns = anchors.columns
    lines: list[ExtractedLine] = []
    for row in _between(rows, anchors.table_row.top, summary_start):
        raw = _description_glyphs(glyphs, row.top, columns.description_limit)
        cells = _cells(row, columns)
        if lines and not any(cell is not None for cell in cells):
            # A continuation row: its raw text keeps a leading space when the break fell
            # on a space, and has none when it fell mid-word ("Tic" + "ket").
            previous = lines[-1]
            lines[-1] = dataclasses.replace(previous, description=previous.description + raw)
            continue
        quantity, unit_price, vat_rate, amount = cells
        lines.append(ExtractedLine(len(lines) + 1, raw, quantity, unit_price, vat_rate, amount))
    return tuple(
        dataclasses.replace(line, description=" ".join(line.description.split())) for line in lines
    )


def _cells(row: _Row, columns: _Columns) -> list[Decimal | None]:
    # Quantity, unit price, VAT rate and amount: each value goes to the column whose
    # heading ends nearest to where the value ends, since cells are right-aligned.
    edges = (columns.quantity, columns.unit_price, columns.vat, columns.amount)
    cells: list[Decimal | None] = [None, None, None, None]
    for word in row.words:
        if word.x0 >= columns.description_limit:
            nearest = min(range(len(edges)), key=lambda index: abs(edges[index] - word.x1))
            cells[nearest] = _number(word.text)
    return cells


def _description_glyphs(glyphs: Sequence[Glyph], top: float, limit: float) -> str:
    row = [g for g in glyphs if abs(g.top - top) <= ROW_TOLERANCE and g.x0 < limit]
    return "".join(g.text for g in sorted(row, key=lambda g: g.x0))


def _summary_start(rows: list[_Row], table_row: _Row) -> float:
    below = [row for row in rows if row.top > table_row.top]
    start = _first(below, lambda row: row.words[0].text.startswith("Subtotal"))
    if start is None:
        start = _first(below, _is_notes)
    return start.top if start else float("inf")


def _summary(rows: list[_Row], start: float, notes_row: _Row | None) -> tuple[SummaryRow, ...]:
    end = notes_row.top if notes_row else float("inf")
    summary = []
    for row in rows:
        if not start <= row.top < end:
            continue
        match = SUMMARY_PATTERN.match(row.text)
        if match:
            amount = _number(match.group("amount"))
            summary.append(SummaryRow(label=match.group("label").strip(), amount=amount))
    return tuple(summary)


def _notes(rows: list[_Row], notes_row: _Row | None) -> str:
    if notes_row is None:
        return ""
    return " ".join(row.text for row in rows if row.top > notes_row.top)


def _is_notes(row: _Row) -> bool:
    return bool(row.words) and row.words[0].text == "Notes"


def _number(text: str) -> Decimal | None:
    # Values are printed as 1,206.00; a VAT rate as 14%. Anything else is not a number.
    candidate = text.removesuffix("%")
    if not AMOUNT_PATTERN.match(candidate):
        return None
    try:
        return Decimal(candidate.replace(",", ""))
    except InvalidOperation:
        return None


def _between(rows: list[_Row], after: float, before: float) -> list[_Row]:
    return [row for row in rows if after < row.top < before]


def _texts(row: _Row) -> list[str]:
    return [word.text for word in row.words]


def _first[Item](items: Iterable[Item], predicate: Callable[[Item], bool]) -> Item | None:
    return next((item for item in items if predicate(item)), None)
