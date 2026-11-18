"""Build the export rows of a job from the persisted state (REQ-EXP-001, REQ-EXP-004).

A read model that composes the published readers of ingestion and matching, so that the
export module reads no other module's tables (02-arquitectura.md §2.1).
"""

from typing import Final

from sqlalchemy.ext.asyncio import AsyncEngine

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
from sextante.matching.contracts import Confidence, exact_entity_match_label
from sextante.platform.user_messages import USER_MESSAGES_PT
from sextante.review.contracts import CodingInForce, CodingsInForce

LINELESS_STATUSES: Final = frozenset({InvoiceStatus.REJECTED, InvoiceStatus.FAILED})
UNKNOWN_REJECTION_KEY: Final = "rejections.other"


def rejection_message(reason: str | None) -> str:
    """Portuguese text of a refusal reason; an unknown reason gets a generic text.

    An export must never fail because one refused document carries an unexpected
    reason (REQ-EXP-007).

    Example:
        rejection_message("pdf_without_text_layer")  # "Documento recusado: PDF ..."
    """
    known = {member.value for member in RejectionReason}
    key = f"rejections.{reason}" if reason in known else UNKNOWN_REJECTION_KEY
    return USER_MESSAGES_PT[key]


class BuildJobExport:
    """Return the rows of a job's export, invoices in upload order, lines in document order.

    Example:
        rows = await BuildJobExport(engine, status, invoices, codings).execute(job_id)
    """

    def __init__(
        self,
        engine: AsyncEngine,
        job_status: ReadJobStatus,
        invoices_reader: InvoiceExportReader,
        codings: CodingsInForce,
    ) -> None:
        self._engine = engine
        self._job_status = job_status
        self._invoices_reader = invoices_reader
        self._codings = codings

    async def execute(self, job_id: str) -> list[ExportRow]:
        """Return the rows; reviewed values are those in force (REQ-EXP-004).

        Example:
            await build_export.execute("3f2a...")

        Raises:
            JobNotFoundError: when no job has this identifier.
        """
        await self._job_status.execute(job_id)
        async with self._engine.connect() as connection:
            invoices = await self._invoices_reader.read_job_invoices(connection, job_id)
            line_ids = [line.line_id for invoice in invoices for line in invoice.lines]
            codings = await self._codings.read(connection, line_ids)
        return [row for invoice in invoices for row in _rows_for(invoice, codings)]


def _rows_for(invoice: ExportInvoice, codings: dict[str, CodingInForce]) -> list[ExportRow]:
    # A refused or failed document still gets one row, so the reviewer sees it existed
    # (REQ-EXP-007). An invoice still waiting has nothing to export yet.
    if invoice.status in LINELESS_STATUSES:
        return [_lineless_row(invoice)]
    return [_line_row(invoice, line, codings.get(line.line_id)) for line in invoice.lines]


def _lineless_row(invoice: ExportInvoice) -> ExportRow:
    notes = (
        rejection_message(invoice.status_reason)
        if invoice.status is InvoiceStatus.REJECTED
        else USER_MESSAGES_PT["export.invoice_failed"]
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


def _line_row(invoice: ExportInvoice, line: ExportLine, coding: CodingInForce | None) -> ExportRow:
    return ExportRow(
        invoice_id=_identifier(invoice),
        billed_entity_detected=invoice.billed_entity or "",
        exact_entity_match=exact_entity_match_label(invoice.entity_verdict),
        target_sheet=(coding.target_sheet or "") if coding else "",
        line_description=line.description,
        assigned_item_no=(coding.item_number or "") if coding else "",
        matched_catalog_description=(coding.catalog_description or "") if coding else "",
        confidence=coding.confidence if coding else Confidence.LOW.value,
        notes_or_flags=_notes(invoice, coding),
    )


def _notes(invoice: ExportInvoice, coding: CodingInForce | None) -> str:
    if coding is None:
        return USER_MESSAGES_PT["export.line_not_coded"]
    texts = [USER_MESSAGES_PT[f"flags.{code}"] for code in coding.flags]
    texts += [USER_MESSAGES_PT[f"notes.{coding.note}"]] if coding.note else []
    texts += [USER_MESSAGES_PT["export.care_of"].format(text) for text in invoice.care_of]
    if coding.review_note:
        texts.append(USER_MESSAGES_PT["export.review_note"].format(coding.review_note))
    return NOTES_SEPARATOR.join(texts)


def _identifier(invoice: ExportInvoice) -> str:
    return invoice_identifier(
        invoice.supplier_nif, invoice.supplier_name, invoice.invoice_number, invoice.content_digest
    )
