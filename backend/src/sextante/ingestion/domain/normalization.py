"""Normalize every text field of an extraction before it is persisted or compared (REQ-ING-008)."""

import dataclasses

from sextante.ingestion.domain.model import (
    BilledEntityBlock,
    ExtractedInvoice,
    ExtractedLine,
    PartyIdentity,
    SummaryRow,
)
from sextante.platform.text_normalization import normalize_text_input


def normalize_extraction(extraction: ExtractedInvoice) -> ExtractedInvoice:
    """Return the same extraction with every text field in NFC and without control characters.

    Extracted text is external input (SEC-09.5): no field skips this, not the billed
    entity, not a tax number, not a summary label.

    Example:
        normalized = normalize_extraction(extraction)
    """
    return dataclasses.replace(
        extraction,
        supplier=_normalize_party(extraction.supplier),
        invoice_number=_optional(extraction.invoice_number),
        invoice_date=_optional(extraction.invoice_date),
        currency=_optional(extraction.currency),
        billed_entities=tuple(_normalize_block(block) for block in extraction.billed_entities),
        lines=tuple(_normalize_line(line) for line in extraction.lines),
        summary_rows=tuple(_normalize_summary(row) for row in extraction.summary_rows),
        notes=normalize_text_input(extraction.notes),
    )


def _normalize_party(party: PartyIdentity) -> PartyIdentity:
    return PartyIdentity(name=_optional(party.name), nif=_optional(party.nif))


def _normalize_block(block: BilledEntityBlock) -> BilledEntityBlock:
    return BilledEntityBlock(
        name=normalize_text_input(block.name),
        nif=_optional(block.nif),
        care_of=tuple(normalize_text_input(text) for text in block.care_of),
        address_lines=tuple(normalize_text_input(text) for text in block.address_lines),
    )


def _normalize_line(line: ExtractedLine) -> ExtractedLine:
    return dataclasses.replace(line, description=normalize_text_input(line.description))


def _normalize_summary(row: SummaryRow) -> SummaryRow:
    return dataclasses.replace(row, label=normalize_text_input(row.label))


def _optional(value: str | None) -> str | None:
    return None if value is None else normalize_text_input(value)
