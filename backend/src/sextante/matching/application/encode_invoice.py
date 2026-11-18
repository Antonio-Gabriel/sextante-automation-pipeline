"""Code the service lines of one routed invoice (REQ-MAP-004 to REQ-MAP-007, SEC-14)."""

import logging
from collections.abc import Sequence
from dataclasses import dataclass

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncEngine

from sextante.catalog.contracts import Catalog, CatalogItem, TargetSheet
from sextante.ingestion.contracts import StoredInvoice, StoredLine
from sextante.matching.application.ports import (
    ItemClassifier,
    LexicalScore,
    LexicalScorer,
    MatchingRepositoryPort,
)
from sextante.matching.application.records import EncodedLineRecord, ModelCallRecord
from sextante.matching.domain.choice_resolution import LineChoice, resolve_line_choices
from sextante.matching.domain.item_choice import (
    CandidateItem,
    InvoiceContext,
    ItemChoiceFromModel,
    ItemChoiceRequest,
    ItemChoiceResponse,
    LineToCode,
)
from sextante.platform.audit import AuditEventRepository
from sextante.platform.clock import Clock, IdentifierGenerator
from sextante.platform.text_normalization import normalize_for_comparison

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class EncodingCollaborators:
    """Everything EncodeInvoice needs, injected (04-padroes-de-codigo.md §4)."""

    engine: AsyncEngine
    catalog: Catalog
    scorer: LexicalScorer
    classifier: ItemClassifier
    repository: MatchingRepositoryPort
    audit: AuditEventRepository
    clock: Clock
    identifiers: IdentifierGenerator


@dataclass(frozen=True, slots=True)
class _InvoiceCoding:
    """What every line of one invoice shares: its routing and its single model call."""

    target_sheet: TargetSheet
    call: ModelCallRecord


class EncodeInvoice:
    """One model call per invoice, then every answer validated and recorded with its audit.

    Example:
        await EncodeInvoice(collaborators).execute(stored_invoice, TargetSheet.OUTLAYS)
    """

    def __init__(self, collaborators: EncodingCollaborators) -> None:
        self._collaborators = collaborators

    async def execute(self, invoice: StoredInvoice, target_sheet: TargetSheet) -> None:
        """Score, ask the model once, resolve answers against the sheet, and persist.

        Example:
            await encoder.execute(stored_invoice, TargetSheet.OUTLAYS)
        """
        deps = self._collaborators
        sheet_items = deps.catalog.items_of(target_sheet)
        scores = {
            line.line_id: deps.scorer.score(line.description, sheet_items) for line in invoice.lines
        }
        # The model call is made outside any transaction: it takes seconds (D-3.3).
        response = await deps.classifier.choose(_request_for(invoice, sheet_items))
        positions = [line.position for line in invoice.lines]
        choices = resolve_line_choices(
            positions, sheet_items, target_sheet, _validated(response.choices)
        )
        call = ModelCallRecord(
            deps.identifiers.new_id(), invoice.invoice_id, response, deps.clock.now()
        )
        await self._persist(invoice, _InvoiceCoding(target_sheet, call), choices, scores)

    async def _persist(
        self,
        invoice: StoredInvoice,
        coding: _InvoiceCoding,
        choices: dict[int, LineChoice],
        scores: dict[str, tuple[LexicalScore, ...]],
    ) -> None:
        deps = self._collaborators
        async with deps.engine.begin() as connection:
            await deps.repository.record_model_call(connection, coding.call)
            for line in invoice.lines:
                record = self._encoded_record(
                    line, choices[line.position], scores[line.line_id], coding
                )
                await deps.repository.record_encoded_line(connection, record)
                await deps.audit.append(
                    connection,
                    deps.identifiers.new_id(),
                    "line_encoded",
                    ("invoice_line", line.line_id),
                    _audit_payload(line, record, coding.call.response),
                    record.encoded_at,
                )

    def _encoded_record(
        self,
        line: StoredLine,
        choice: LineChoice,
        scores: tuple[LexicalScore, ...],
        coding: _InvoiceCoding,
    ) -> EncodedLineRecord:
        deps = self._collaborators
        return EncodedLineRecord(
            encoded_line_id=deps.identifiers.new_id(),
            invoice_line_id=line.line_id,
            target_sheet=coding.target_sheet,
            choice=choice,
            scores=scores,
            catalog_digest=str(deps.catalog.digest),
            model_call_id=coding.call.call_id,
            encoded_at=deps.clock.now(),
        )


def _validated(choices: Sequence[ItemChoiceFromModel]) -> list[ItemChoiceFromModel]:
    # Every answer goes through the schema again, whatever the adapter did: an answer
    # that fails it is dropped, and its line becomes an invalid response (SEC-14, REQ-MAP-007).
    valid: list[ItemChoiceFromModel] = []
    for choice in choices:
        try:
            valid.append(ItemChoiceFromModel.model_validate(choice.model_dump()))
        except ValidationError:
            logger.warning(
                "model_answer_rejected_by_schema", extra={"line_position": choice.line_position}
            )
    return valid


def _request_for(invoice: StoredInvoice, sheet_items: tuple[CatalogItem, ...]) -> ItemChoiceRequest:
    return ItemChoiceRequest(
        context=InvoiceContext(supplier_name=invoice.supplier_name, currency=invoice.currency),
        lines=tuple(LineToCode(line.position, line.description) for line in invoice.lines),
        candidates=tuple(
            CandidateItem(
                index,
                catalog_item.item_number.value,
                catalog_item.description_pt,
                catalog_item.description_en,
            )
            for index, catalog_item in enumerate(sheet_items)
        ),
    )


def _audit_payload(
    line: StoredLine, record: EncodedLineRecord, response: ItemChoiceResponse
) -> dict[str, object]:
    # The audit trail lives in the database, with its own access and retention, so it
    # keeps the description that fed the decision; the log does not (REQ-AUD-001, SEC-15).
    catalog_item = record.choice.catalog_item
    return {
        "description": line.description,
        "normalized_description": normalize_for_comparison(line.description),
        "target_sheet": record.target_sheet.value,
        "choice_outcome": record.choice.outcome.value,
        "candidate_index": record.choice.candidate_index,
        "item_number": catalog_item.item_number.value if catalog_item else None,
        "scores": [[score.item_number, score.score] for score in record.scores],
        "model_id": response.model_id,
        "prompt_version": response.prompt_version,
        "catalog_digest": record.catalog_digest,
        "encoded_at": record.encoded_at.isoformat(),
    }
