"""Manual measurement of item codes with the REAL model on the local samples (ticket 13).

Not part of ``make test`` nor of continuous integration: it calls the Anthropic API and
costs money. Run it on purpose, with ``make golden-model``, from backend/.

It codes the samples with the application's own LineCoder, coding rules and API client
(same request, retries, validation and confidence rule), and compares the item numbers
with the expected results. The report holds sample identifiers, line positions, item
numbers and confidence only; no text from a sample. The expected results are a proposal
until AMT confirms them (L-02), so the figures are for calibration, never for publication.
"""

import asyncio
import os
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields
from pathlib import Path

from anthropic import APIStatusError, AsyncAnthropic

from sextante.catalog.application.load_catalog import CatalogFileError, load_catalog
from sextante.catalog.domain.errors import CatalogValidationError
from sextante.catalog.infrastructure.xlsx_catalog_reader import XlsxCatalogWorkbookReader
from sextante.ingestion.domain.line_type import classify_line_type
from sextante.ingestion.domain.model import ExtractedInvoice, FileFormat, StoredInvoice, StoredLine
from sextante.ingestion.domain.normalization import normalize_extraction
from sextante.ingestion.infrastructure.pdf_invoice_extractor import PdfInvoiceExtractor
from sextante.main import coding_rules
from sextante.matching.application.line_coding import LineCoder, LineOutcome
from sextante.matching.contracts import (
    ItemClassifierUnavailableError,
    check_billed_entity,
    target_sheet_for,
)
from sextante.matching.domain.item_choice import ItemChoiceResponse
from sextante.matching.infrastructure.claude_classifier import (
    ClaudeItemClassifier,
    create_model_client,
)
from sextante.platform.settings import ModelCallSettings, StartupConfigurationError
from tests.golden.runner import (
    EntityReference,
    ExpectedLine,
    GoldenSetError,
    GoldenSettings,
    SampleExpectation,
    entity_reference,
    load_expectations,
    sample_file,
)


class ModelRunSettings(GoldenSettings, ModelCallSettings):
    """The golden set variables, plus the model call's, read like the application's."""

    catalog_path: Path


@dataclass(frozen=True, slots=True)
class TokenUsage:
    """Tokens spent on model calls: uncached input, output, and cache writes and reads."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_written: int = 0
    cache_read: int = 0

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            *(getattr(self, f.name) + getattr(other, f.name) for f in fields(TokenUsage))
        )

    @classmethod
    def of(cls, response: ItemChoiceResponse | None) -> "TokenUsage":
        """The tokens of one model call, or none when no call was made.

        Example:
            TokenUsage.of(coded.response).cache_read
        """
        if response is None:
            return cls()
        return cls(
            response.input_tokens,
            response.output_tokens,
            response.cache_creation_input_tokens,
            response.cache_read_input_tokens,
        )


@dataclass(frozen=True, slots=True)
class LineResult:
    """One expected line: what was expected, what the system assigned, and how."""

    sample_id: str
    position: int
    expected: str
    assigned: str | None
    confidence: str | None
    flagged: bool
    note: str = ""


@dataclass(frozen=True, slots=True)
class _Coding:
    coder: LineCoder
    client: AsyncAnthropic
    entity: EntityReference


async def measure_sample(
    coding: _Coding, expectation: SampleExpectation, extraction: ExtractedInvoice
) -> tuple[list[LineResult], TokenUsage]:
    """Code one sample with the application's LineCoder; return its lines and tokens.

    Example:
        results, usage = await measure_sample(coding, expectation, extraction)
    """
    invoice = normalize_extraction(extraction)
    entity = coding.entity
    verdict = check_billed_entity(invoice.billed_entities, entity.target, entity.denylist).verdict
    sheet = target_sheet_for(verdict)
    if sheet is None:
        return _unassigned(expectation, "no target sheet"), TokenUsage()
    try:
        coded = await coding.coder.code(_stored(expectation.id, invoice), sheet)
    except ItemClassifierUnavailableError:
        return _unassigned(expectation, "model unavailable"), TokenUsage()
    by_position = {outcome.line.position: outcome for outcome in coded.outcomes}
    results = [_line_result(expectation.id, line, by_position) for line in expectation.lines]
    response = coded.response
    usage = TokenUsage.of(response)
    return results, usage


def _line_result(
    sample_id: str, expected: ExpectedLine, by_position: Mapping[int, LineOutcome]
) -> LineResult:
    outcome = by_position.get(expected.position)
    if outcome is None:
        return LineResult(
            sample_id, expected.position, expected.item_number, None, None, True, "line not found"
        )
    decision = outcome.decision
    assigned = decision.catalog_item.item_number.value if decision.catalog_item else None
    return LineResult(
        sample_id,
        expected.position,
        expected.item_number,
        assigned,
        decision.confidence.value,
        bool(decision.flags),
    )


def _unassigned(expectation: SampleExpectation, note: str) -> list[LineResult]:
    return [
        LineResult(expectation.id, line.position, line.item_number, None, None, True, note)
        for line in expectation.lines
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


def report(results: list[LineResult], usage: TokenUsage) -> list[str]:
    """One line per expected line, then the totals: codes and confidence only.

    Example:
        report(results, TokenUsage(500, 400, 1900, 17100))[-2]  # "Tokens: 500 in, ..."
    """
    lines = [
        f"{r.sample_id} line {r.position}: expected {r.expected}, assigned {r.assigned or '-'}, "
        f"{r.confidence or '-'}{', flagged' if r.flagged else ''}{f' ({r.note})' if r.note else ''}"
        for r in results
    ]
    hits = sum(1 for r in results if r.assigned == r.expected)
    flagged = sum(1 for r in results if r.flagged)
    return [
        *lines,
        f"{len(results)} lines, {hits} as expected, {flagged} flagged for review",
        f"Tokens: {usage.input_tokens} in, {usage.output_tokens} out, "
        f"{usage.cache_written} written to cache, {usage.cache_read} read from cache",
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
        results, usage = await _measure_all(settings, coding)
    except APIStatusError as error:
        # The API's own message (a key or billing problem); it carries no invoice text.
        write(f"The Anthropic API refused the request ({error.status_code}): {error.message}")
        return 2
    finally:
        await coding.client.close()
    for line in report(results, usage):
        write(line)
    return 0


async def _measure_all(
    settings: ModelRunSettings, coding: _Coding
) -> tuple[list[LineResult], TokenUsage]:
    extractor = PdfInvoiceExtractor(settings.pdf_min_chars_per_page)
    results: list[LineResult] = []
    usage = TokenUsage()
    for expectation in load_expectations(settings.expected_path).samples:
        sample = sample_file(settings.samples_path, expectation.id)
        if expectation.rejected is not None or sample is None:
            continue
        extraction = extractor.extract(sample.read_bytes(), FileFormat.PDF)
        if isinstance(extraction, ExtractedInvoice):
            sample_results, sample_usage = await measure_sample(coding, expectation, extraction)
            results += sample_results
            usage += sample_usage
    return results, usage


def _coding(settings: ModelRunSettings) -> _Coding:
    # The same client, rules and coder the application builds: only the samples differ.
    try:
        catalog = load_catalog(settings.catalog_path, XlsxCatalogWorkbookReader()).catalog
    except (CatalogFileError, CatalogValidationError) as error:
        raise GoldenSetError(f"SEXTANTE_CATALOG_PATH: {error}") from None
    client = create_model_client(settings.anthropic_api_key.get_secret_value())
    classifier = ClaudeItemClassifier(client, settings.model_id)
    try:
        rules = coding_rules(
            catalog, classifier, settings.generic_items, settings.model_max_attempts, asyncio.sleep
        )
    except StartupConfigurationError as error:
        raise GoldenSetError(str(error)) from None
    return _Coding(LineCoder(rules), client, entity_reference(settings))


if __name__ == "__main__":
    sys.exit(asyncio.run(run(os.environ, print)))
