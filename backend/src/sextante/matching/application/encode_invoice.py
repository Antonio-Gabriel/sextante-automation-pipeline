"""Code the service lines of one routed invoice (REQ-MAP-004 to REQ-MAP-007, SEC-14)."""

from dataclasses import dataclass

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
    ItemChoiceRequest,
    ItemChoiceResponse,
    LineToCode,
)
from sextante.platform.audit import AuditEventRepository
from sextante.platform.clock import Clock, IdentifierGenerator
from sextante.platform.text_normalization import normalize_for_comparison


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


class EncodeInvoice:
    """One model call per invoice, then every answer validated and recorded with its audit.

    Example:
        await EncodeInvoice(collaborators).execute(stored_invoice, TargetSheet.OUTLAYS)
    """

    def __init__(self, collaborators: EncodingCollaborators) -> None:
        self._with = collaborators

    async def execute(self, invoice: StoredInvoice, target_sheet: TargetSheet) -> None:
        """Score, ask the model once, resolve answers against the sheet, and persist."""
        sheet_items = self._with.catalog.items_of(target_sheet)
        scores = {
            line.line_id: self._with.scorer.score(line.description, sheet_items)
            for line in invoice.lines
        }
        # The model call is made outside any transaction: it takes seconds (D-3.3).
        response = await self._with.classifier.choose(_request_for(invoice.lines, sheet_items))
        choices = resolve_line_choices(
            [line.position for line in invoice.lines], sheet_items, target_sheet, response.choices
        )
        await self._persist(invoice, target_sheet, response, choices, scores)

    async def _persist(
        self,
        invoice: StoredInvoice,
        target_sheet: TargetSheet,
        response: ItemChoiceResponse,
        choices: dict[int, LineChoice],
        scores: dict[str, tuple[LexicalScore, ...]],
    ) -> None:
        call = ModelCallRecord(
            self._with.identifiers.new_id(), invoice.invoice_id, response, self._with.clock.now()
        )
        async with self._with.engine.begin() as connection:
            await self._with.repository.record_model_call(connection, call)
            for line in invoice.lines:
                record = self._line_record(
                    line, target_sheet, choices[line.position], scores[line.line_id], call
                )
                await self._with.repository.record_encoded_line(connection, record)
                await self._with.audit.append(
                    connection,
                    self._with.identifiers.new_id(),
                    "line_encoded",
                    ("invoice_line", line.line_id),
                    _audit_payload(line, record, response),
                    record.encoded_at,
                )

    def _line_record(
        self,
        line: StoredLine,
        target_sheet: TargetSheet,
        choice: LineChoice,
        scores: tuple[LexicalScore, ...],
        call: ModelCallRecord,
    ) -> EncodedLineRecord:
        return EncodedLineRecord(
            encoded_line_id=self._with.identifiers.new_id(),
            invoice_line_id=line.line_id,
            target_sheet=target_sheet.value,
            choice=choice,
            scores=scores,
            catalog_digest=str(self._with.catalog.digest),
            model_call_id=call.call_id,
            encoded_at=self._with.clock.now(),
        )


def _request_for(
    lines: tuple[StoredLine, ...], sheet_items: tuple[CatalogItem, ...]
) -> ItemChoiceRequest:
    return ItemChoiceRequest(
        lines=tuple(LineToCode(line.position, line.description) for line in lines),
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
        "target_sheet": record.target_sheet,
        "choice_outcome": record.choice.outcome.value,
        "candidate_index": record.choice.candidate_index,
        "item_number": catalog_item.item_number.value if catalog_item else None,
        "top_scores": [[s.item_number, s.score] for s in record.scores[:3]],
        "model_id": response.model_id,
        "prompt_version": response.prompt_version,
        "catalog_digest": record.catalog_digest,
        "encoded_at": record.encoded_at.isoformat(),
    }
