"""Manual measurement of item codes with the REAL model on the local samples (ticket 13).

Not part of ``make test`` nor of continuous integration: it calls the Anthropic API and
costs money. Run it on purpose, with ``make golden-model``, from backend/.

It codes the samples as the application does (same request, same validation, same
confidence rule) and compares the item numbers with the expected results. The report
holds sample identifiers, line positions, item numbers and confidence only; no text
from a sample. The expected results are a proposal until AMT confirms them (L-02), so
the figures are for calibration, never for publication.
"""

import asyncio
import os
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from anthropic import APIStatusError, AsyncAnthropic
from pydantic import SecretStr, field_validator

from sextante.catalog.application.load_catalog import CatalogFileError, load_catalog
from sextante.catalog.contracts import (
    FALLBACK_ITEM_NUMBER,
    Catalog,
    CatalogItem,
    ItemNumber,
    TargetSheet,
)
from sextante.catalog.domain.errors import CatalogValidationError
from sextante.catalog.infrastructure.xlsx_catalog_reader import XlsxCatalogWorkbookReader
from sextante.ingestion.domain.line_type import LineType, classify_line_type
from sextante.ingestion.domain.model import ExtractedInvoice, FileFormat, StoredInvoice, StoredLine
from sextante.ingestion.domain.normalization import normalize_extraction
from sextante.ingestion.infrastructure.pdf_invoice_extractor import PdfInvoiceExtractor
from sextante.matching.application.encode_invoice import item_choice_request
from sextante.matching.contracts import (
    ItemClassifierUnavailableError,
    check_billed_entity,
    target_sheet_for,
)
from sextante.matching.domain.choice_resolution import LineChoice, resolve_line_choices
from sextante.matching.domain.line_decision import decide_line
from sextante.matching.infrastructure.claude_classifier import ClaudeItemClassifier
from sextante.matching.infrastructure.rapidfuzz_scorer import RapidfuzzLexicalScorer
from tests.golden.runner import (
    EntityReference,
    GoldenSetError,
    GoldenSettings,
    SampleExpectation,
    entity_reference,
    load_expectations,
    sample_file,
)

MODEL_TIMEOUT_SECONDS: Final = 120.0


class ModelRunSettings(GoldenSettings):
    """The golden set variables, plus what a real model call needs."""

    catalog_path: Path
    anthropic_api_key: SecretStr
    model_id: str = "claude-opus-5-5"
    generic_items: tuple[str, ...] = ("O00052",)

    @field_validator("generic_items", mode="before")
    @classmethod
    def _split(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(part.strip() for part in value.split(",") if part.strip())
        return value


@dataclass(frozen=True, slots=True)
class LineResult:
    """One expected line: what was expected, what the system assigned, and how."""

    sample_id: str
    position: int
    expected: str
    assigned: str | None
    confidence: str
    flagged: bool


@dataclass(frozen=True, slots=True)
class _Coding:
    catalog: Catalog
    fallback: CatalogItem
    client: AsyncAnthropic
    classifier: ClaudeItemClassifier
    entity: EntityReference
    generic_items: frozenset[ItemNumber]


async def measure_sample(
    coding: _Coding, expectation: SampleExpectation, extraction: ExtractedInvoice
) -> tuple[list[LineResult], tuple[int, int]]:
    """Code one sample as the application would; return its lines and the tokens spent.

    Example:
        results, (tokens_in, tokens_out) = await measure_sample(coding, expectation, ext)
    """
    invoice = normalize_extraction(extraction)
    entity = coding.entity
    verdict = check_billed_entity(invoice.billed_entities, entity.target, entity.denylist).verdict
    sheet = target_sheet_for(verdict)
    if sheet is None:
        return _unassigned(expectation, "no target sheet"), (0, 0)
    stored = _stored(expectation.id, invoice)
    services = [line for line in stored.lines if line.line_type is LineType.SERVICE]
    items = coding.catalog.items_of(sheet)
    try:
        response = await coding.classifier.choose(item_choice_request(stored, services, items))
    except ItemClassifierUnavailableError:
        return _unassigned(expectation, "model unavailable"), (0, 0)
    choices = resolve_line_choices([s.position for s in services], items, sheet, response.choices)
    results = [
        _line_result(coding, expectation, sheet, line, choices[line.position]) for line in services
    ]
    return results, (response.input_tokens, response.output_tokens)


def _line_result(
    coding: _Coding,
    expectation: SampleExpectation,
    sheet: TargetSheet,
    line: StoredLine,
    choice: LineChoice,
) -> LineResult:
    scores = RapidfuzzLexicalScorer().score(line.description, coding.catalog.items_of(sheet))
    decision = decide_line(choice, sheet, scores, coding.fallback, coding.generic_items)
    expected = {e.position: e.item_number for e in expectation.lines}.get(line.position, "")
    assigned = decision.catalog_item.item_number.value if decision.catalog_item else None
    return LineResult(
        expectation.id,
        line.position,
        expected,
        assigned,
        decision.confidence.value,
        bool(decision.flags),
    )


def _unassigned(expectation: SampleExpectation, reason: str) -> list[LineResult]:
    return [
        LineResult(expectation.id, e.position, e.item_number, None, reason, True)
        for e in expectation.lines
    ]


def _stored(sample_id: str, invoice: ExtractedInvoice) -> StoredInvoice:
    lines = tuple(
        StoredLine(
            f"{sample_id}-{line.position}",
            line.position,
            line.description,
            classify_line_type(line.description),
        )
        for line in invoice.lines
    )
    return StoredInvoice(
        f"golden-{sample_id}",
        invoice.supplier.name,
        invoice.currency,
        invoice.billed_entities,
        lines,
    )


def report(results: list[LineResult], tokens: tuple[int, int]) -> list[str]:
    """One line per expected line, then the totals: codes and confidence only.

    Example:
        report(results, (12000, 400))[-1]  # "Tokens: 12000 in, 400 out"
    """
    lines = [
        f"{r.sample_id} line {r.position}: expected {r.expected}, assigned {r.assigned or '-'}, "
        f"{r.confidence}{', flagged' if r.flagged else ''}"
        for r in results
    ]
    hits = sum(1 for r in results if r.assigned == r.expected)
    flagged = sum(1 for r in results if r.flagged)
    return [
        *lines,
        f"{len(results)} lines, {hits} as expected, {flagged} flagged for review",
        f"Tokens: {tokens[0]} in, {tokens[1]} out",
        "Expected results are a proposal to be confirmed by AMT (L-02): not for publication.",
    ]


async def run(environ: Mapping[str, str], write: Callable[[str], None]) -> int:
    """Measure every coded sample with the real model.

    Returns 2, with a clear message, on a configuration error or when the API refuses the
    request (a bad key, no credit); never a traceback.

    Example:
        sys.exit(asyncio.run(run(os.environ, print)))
    """
    try:
        settings = ModelRunSettings.from_environment(environ)
        coding = _coding(settings)
    except GoldenSetError as error:
        write(str(error))
        return 2
    try:
        results, tokens = await _measure_all(settings, coding)
    except APIStatusError as error:
        # The API's own message (a key or billing problem); it carries no invoice text.
        write(f"The Anthropic API refused the request ({error.status_code}): {error.message}")
        return 2
    finally:
        await coding.client.close()
    for line in report(results, tokens):
        write(line)
    return 0


async def _measure_all(
    settings: ModelRunSettings, coding: _Coding
) -> tuple[list[LineResult], tuple[int, int]]:
    extractor = PdfInvoiceExtractor(settings.pdf_min_chars_per_page)
    results: list[LineResult] = []
    used_in = used_out = 0
    for expectation in load_expectations(settings.expected_path).samples:
        sample = sample_file(settings.samples_path, expectation.id)
        if expectation.rejected is not None or sample is None:
            continue
        extraction = extractor.extract(sample.read_bytes(), FileFormat.PDF)
        if isinstance(extraction, ExtractedInvoice):
            sample_results, (tokens_in, tokens_out) = await measure_sample(
                coding, expectation, extraction
            )
            results += sample_results
            used_in, used_out = used_in + tokens_in, used_out + tokens_out
    return results, (used_in, used_out)


def _coding(settings: ModelRunSettings) -> _Coding:
    try:
        catalog = load_catalog(settings.catalog_path, XlsxCatalogWorkbookReader()).catalog
    except (CatalogFileError, CatalogValidationError) as error:
        raise GoldenSetError(f"SEXTANTE_CATALOG_PATH: {error}") from None
    client = AsyncAnthropic(
        api_key=settings.anthropic_api_key.get_secret_value(),
        max_retries=2,
        timeout=MODEL_TIMEOUT_SECONDS,
    )
    fallback = catalog.find(FALLBACK_ITEM_NUMBER)
    if fallback is None:
        raise GoldenSetError(f"Invalid catalog: no item {FALLBACK_ITEM_NUMBER}. Expected it.")
    generic = frozenset(ItemNumber(n) for n in settings.generic_items)
    classifier = ClaudeItemClassifier(client, settings.model_id)
    return _Coding(catalog, fallback, client, classifier, entity_reference(settings), generic)


if __name__ == "__main__":
    sys.exit(asyncio.run(run(os.environ, print)))
