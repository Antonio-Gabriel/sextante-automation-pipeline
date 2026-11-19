"""Build the export rows of a job from the persisted state (REQ-EXP-001, REQ-EXP-004).

A read model that composes the published readers of ingestion and matching, so that the
export module reads no other module's tables (02-arquitectura.md §2.1).
"""

from dataclasses import dataclass
from typing import Final

from sqlalchemy.ext.asyncio import AsyncEngine

from sextante.catalog.contracts import Catalog
from sextante.export.domain.export_rows import NOTES_SEPARATOR, ExportRow
from sextante.export.domain.invoice_identifier import invoice_identifier
from sextante.ingestion.contracts import (
    ExportInvoice,
    ExportLine,
    InvoiceExportReader,
    InvoiceStatus,
    ReadJobStatus,
    RejectionReason,
)
from sextante.matching.contracts import (
    Confidence,
    FlagReason,
    entity_notes,
    exact_entity_match_label,
)
from sextante.platform.language import Language
from sextante.platform.user_messages import user_message
from sextante.review.contracts import CodingInForce, CodingsInForce

LINELESS_STATUSES: Final = frozenset({InvoiceStatus.REJECTED, InvoiceStatus.FAILED})
UNKNOWN_REJECTION_KEY: Final = "rejections.other"
DATE_FORMAT: Final = "%d-%m-%Y"


@dataclass(frozen=True, slots=True)
class _Texts:
    # The language of one export: its messages, and the catalog's descriptions in it.
    language: Language
    catalog: Catalog

    def message(self, key: str) -> str:
        return user_message(key, self.language)

    def description(self, coding: CodingInForce) -> str:
        recorded = coding.catalog_description
        return self.catalog.description_in(coding.item_number, self.language, recorded) or ""


def rejection_message(reason: str | None, language: Language) -> str:
    """The text of a refusal reason; an unknown reason gets a generic text.

    An export must never fail because one refused document carries an unexpected
    reason (REQ-EXP-007).

    Example:
        rejection_message("pdf_without_text_layer", Language.EN)  # "Document refused: ..."
    """
    known = {member.value for member in RejectionReason}
    key = f"rejections.{reason}" if reason in known else UNKNOWN_REJECTION_KEY
    return user_message(key, language)


class BuildJobExport:
    """Return the rows of a job's export, invoices in upload order, lines in document order.

    Example:
        rows = await BuildJobExport(engine, status, invoices, codings, catalog).execute(
            job_id, Language.EN
        )
    """

    def __init__(
        self,
        engine: AsyncEngine,
        job_status: ReadJobStatus,
        invoices_reader: InvoiceExportReader,
        codings: CodingsInForce,
        catalog: Catalog,
    ) -> None:
        self._engine = engine
        self._job_status = job_status
        self._invoices_reader = invoices_reader
        self._codings = codings
        self._catalog = catalog

    async def execute(self, job_id: str, language: Language) -> list[ExportRow]:
        """Return the rows, texts in the language; reviewed values in force (REQ-EXP-004).

        Example:
            await build_export.execute("3f2a...", Language.PT)

        Raises:
            JobNotFoundError: when no job has this identifier.
        """
        await self._job_status.execute(job_id)
        async with self._engine.connect() as connection:
            invoices = await self._invoices_reader.read_job_invoices(connection, job_id)
            line_ids = [line.line_id for invoice in invoices for line in invoice.lines]
            codings = await self._codings.read(connection, line_ids)
        texts = _Texts(language, self._catalog)
        return [row for invoice in invoices for row in _rows_for(invoice, codings, texts)]


def _rows_for(
    invoice: ExportInvoice, codings: dict[str, CodingInForce], texts: _Texts
) -> list[ExportRow]:
    # A refused or failed document still gets one row, so the reviewer sees it existed
    # (REQ-EXP-007). An invoice still waiting has nothing to export yet.
    if invoice.status in LINELESS_STATUSES:
        return [_lineless_row(invoice, texts)]
    return [_line_row(invoice, line, codings.get(line.line_id), texts) for line in invoice.lines]


def _lineless_row(invoice: ExportInvoice, texts: _Texts) -> ExportRow:
    notes = (
        rejection_message(invoice.status_reason, texts.language)
        if invoice.status is InvoiceStatus.REJECTED
        else texts.message("export.invoice_failed")
    )
    return ExportRow(
        invoice_id=_identifier(invoice),
        billed_entity_detected=invoice.billed_entity or "",
        exact_entity_match="NO",
        target_sheet="",
        line_description="",
        assigned_item_no="",
        matched_catalog_description="",
        # REQ-EXP-007 sets LOW for a document that could not be coded at all.
        confidence=Confidence.LOW.value,
        notes_or_flags=notes,
    )


def _line_row(
    invoice: ExportInvoice, line: ExportLine, coding: CodingInForce | None, texts: _Texts
) -> ExportRow:
    return ExportRow(
        invoice_id=_identifier(invoice),
        billed_entity_detected=invoice.billed_entity or "",
        exact_entity_match=exact_entity_match_label(invoice.entity_verdict, invoice.entity_reason),
        target_sheet=(coding.target_sheet or "") if coding else "",
        line_description=line.description,
        assigned_item_no=(coding.item_number or "") if coding else "",
        matched_catalog_description=texts.description(coding) if coding else "",
        confidence=coding.confidence if coding else Confidence.LOW.value,
        notes_or_flags=_notes(invoice, coding, texts),
    )


def _notes(invoice: ExportInvoice, coding: CodingInForce | None, texts: _Texts) -> str:
    if coding is None:
        return texts.message("export.line_not_coded")
    notes = [_flag_text(invoice, code, texts) for code in coding.flags]
    notes += [texts.message(f"notes.{coding.note}")] if coding.note else []
    notes += [
        texts.message(f"notes.{code}")
        for code in entity_notes(invoice.entity_verdict, invoice.entity_reason)
    ]
    notes += [texts.message("export.care_of").format(text) for text in invoice.care_of]
    if coding.review_note:
        notes.append(texts.message("export.review_note").format(coding.review_note))
    return NOTES_SEPARATOR.join(notes)


def _flag_text(invoice: ExportInvoice, code: str, texts: _Texts) -> str:
    # A possible duplicate names the earlier copy as a person knows it: the file and the
    # day it was uploaded. Both copies share the Invoice_ID, so it would not tell them apart.
    earlier = invoice.earlier_copy
    if code == FlagReason.POSSIBLE_DUPLICATE.value and earlier is not None:
        uploaded_on = earlier.uploaded_at.strftime(DATE_FORMAT)
        return texts.message("export.possible_duplicate_of").format(earlier.file_name, uploaded_on)
    return texts.message(f"flags.{code}")


def _identifier(invoice: ExportInvoice) -> str:
    return invoice_identifier(
        invoice.supplier_nif, invoice.supplier_name, invoice.invoice_number, invoice.content_digest
    )
