"""Golden set: the deterministic steps measured on the sample invoices (NFR-TST-001, D-3.18).

Measures extraction, entity, target sheet, line types and refusals, without calling the
model. The samples are read from a local folder and never enter the repository; the
report names samples, fields and closed-set values only, never text from a sample.

Expected results are a proposal until AMT confirms them (L-02), so no accuracy figure
is published from this report.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from sextante.ingestion.domain.line_type import classify_line_type
from sextante.ingestion.domain.model import ExtractedInvoice, ExtractionRejection, FileFormat
from sextante.ingestion.domain.normalization import normalize_extraction
from sextante.ingestion.domain.ports import InvoiceExtractor
from sextante.ingestion.infrastructure.pdf_invoice_extractor import PdfInvoiceExtractor
from sextante.matching.contracts import (
    EntityDenylist,
    TargetEntity,
    check_billed_entity,
    target_sheet_for,
)
from sextante.matching.infrastructure.denylist_file import DenylistFileError, read_entity_denylist

SAMPLES_DIR_VARIABLE: Final = "SEXTANTE_GOLDEN_SAMPLES_DIR"
EXPECTED_PATH_VARIABLE: Final = "SEXTANTE_GOLDEN_EXPECTED_PATH"
# backend/src/sextante/ -> the repository root holds config/.
DEFAULT_EXPECTED_PATH: Final = (
    Path(__file__).resolve().parents[3] / "config" / "golden_expected.yaml"
)
DEFAULT_MIN_CHARS: Final = 100
ENTITY_VARIABLES: Final = (
    "SEXTANTE_TARGET_ENTITY_NAME",
    "SEXTANTE_TARGET_ENTITY_NIF",
    "SEXTANTE_ENTITY_DENYLIST_PATH",
)


class GoldenSetError(RuntimeError):
    """The golden set cannot run: missing folder, or an unreadable expected-results file."""


class ExpectedLine(BaseModel):
    """One line of a sample, named by position: never by its description."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    position: int = Field(ge=1)
    line_type: Literal["service", "tax", "discount"]
    item_number: str


class SampleExpectation(BaseModel):
    """What one sample should give: a refusal, or an entity, a sheet and its lines."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^[A-Za-z0-9-]{1,32}$")
    rejected: Literal["pdf_without_text_layer", "unsupported_document_type"] | None = None
    entity: Literal["MATCH", "NO_MATCH", "AMBIGUOUS"] | None = None
    target_sheet: Literal["OUTLAYS", "OUTLAYSP"] | None = None
    lines: tuple[ExpectedLine, ...] = ()


class GoldenExpectations(BaseModel):
    """The expected-results file."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal[1]
    proposal: bool
    samples: tuple[SampleExpectation, ...]


@dataclass(frozen=True, slots=True)
class SampleResult:
    """One sample's divergences; none means it matched what is expected."""

    sample_id: str
    divergences: tuple[str, ...]


def load_expectations(path: Path) -> GoldenExpectations:
    """Read and validate the expected-results file.

    Example:
        load_expectations(Path("config/golden_expected.yaml")).samples[0].id  # "INV-001"

    Raises:
        GoldenSetError: when the file is missing or does not match the schema.
    """
    try:
        return GoldenExpectations.model_validate(yaml.safe_load(path.read_text("utf-8")))
    except (OSError, yaml.YAMLError, ValidationError) as error:
        raise GoldenSetError(
            f"Expected results {path} are unreadable ({type(error).__name__}). "
            "Expected the format of config/golden_expected.yaml."
        ) from None


def run_golden(
    samples_dir: Path,
    expectations: GoldenExpectations,
    extractor: InvoiceExtractor,
    entity: tuple[TargetEntity, EntityDenylist],
) -> list[SampleResult]:
    """Measure every expected sample found in the folder.

    Example:
        results = run_golden(Path("/samples"), expectations, extractor, (target, denylist))

    Raises:
        GoldenSetError: when the folder does not exist.
    """
    if not samples_dir.is_dir():
        raise GoldenSetError(f"Samples folder {samples_dir} does not exist. Expected a folder.")
    results = []
    for expectation in expectations.samples:
        sample = _sample_file(samples_dir, expectation.id)
        if sample is None:
            results.append(SampleResult(expectation.id, ("sample file not found",)))
            continue
        extraction = extractor.extract(sample.read_bytes(), FileFormat.PDF)
        results.append(SampleResult(expectation.id, _divergences(expectation, extraction, entity)))
    return results


def report_lines(results: Sequence[SampleResult]) -> list[str]:
    """One line per sample, then the count: identifiers and field names only.

    Example:
        report_lines(results)  # ["INV-001 ok", ..., "12 samples, 0 with divergences"]
    """
    lines = [
        f"{r.sample_id} ok" if not r.divergences else f"{r.sample_id} " + "; ".join(r.divergences)
        for r in results
    ]
    failed = sum(1 for r in results if r.divergences)
    return [*lines, f"{len(results)} samples, {failed} with divergences"]


def _sample_file(samples_dir: Path, sample_id: str) -> Path | None:
    matches = sorted(
        path
        for path in samples_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() == ".pdf"
        and (path.stem == sample_id or path.stem.startswith(f"{sample_id}_"))
    )
    return matches[0] if matches else None


def _divergences(
    expectation: SampleExpectation,
    extraction: ExtractedInvoice | ExtractionRejection,
    entity: tuple[TargetEntity, EntityDenylist],
) -> tuple[str, ...]:
    if isinstance(extraction, ExtractionRejection):
        got = extraction.reason.value
        return (
            () if got == expectation.rejected else (_differs("refusal", expectation.rejected, got),)
        )
    if expectation.rejected is not None:
        return (_differs("refusal", expectation.rejected, None),)
    return tuple(_coded_divergences(expectation, normalize_extraction(extraction), entity))


def _coded_divergences(
    expectation: SampleExpectation,
    extraction: ExtractedInvoice,
    entity: tuple[TargetEntity, EntityDenylist],
) -> list[str]:
    target, denylist = entity
    verdict = check_billed_entity(extraction.billed_entities, target, denylist).verdict
    sheet = target_sheet_for(verdict)
    got: Mapping[str, object] = {
        "entity": verdict.value,
        "target_sheet": sheet.value if sheet else None,
        "line count": len(extraction.lines),
        "line types": [classify_line_type(line.description).value for line in extraction.lines],
    }
    expected: Mapping[str, object] = {
        "entity": expectation.entity,
        "target_sheet": expectation.target_sheet,
        "line count": len(expectation.lines),
        "line types": [line.line_type for line in expectation.lines],
    }
    return [
        _differs(name, expected[name], got[name]) for name in got if got[name] != expected[name]
    ]


def _differs(field: str, expected: object, got: object) -> str:
    return f"{field}: expected {expected}, got {got}"


def golden_main(environ: Mapping[str, str], write: Callable[[str], None]) -> int:
    """Run the golden set from SEXTANTE_ variables; 0 when every sample matches.

    Returns 2, with a clear message, when the samples folder is not configured or the
    configuration cannot be read; 1 when a sample diverges.

    Example:
        sys.exit(golden_main(os.environ, print))
    """
    try:
        samples_dir, expectations, extractor, entity = _configured(environ)
        results = run_golden(samples_dir, expectations, extractor, entity)
    except GoldenSetError as error:
        write(str(error))
        return 2
    for line in report_lines(results):
        write(line)
    if expectations.proposal:
        write("Expected results are a proposal still to be confirmed by AMT (L-02).")
    return 1 if any(result.divergences for result in results) else 0


def _configured(
    environ: Mapping[str, str],
) -> tuple[Path, GoldenExpectations, InvoiceExtractor, tuple[TargetEntity, EntityDenylist]]:
    samples = environ.get(SAMPLES_DIR_VARIABLE, "").strip()
    if not samples:
        raise GoldenSetError(
            f"{SAMPLES_DIR_VARIABLE} is not set. Expected the local folder with the sample "
            "invoices, which never enter the repository."
        )
    expectations = load_expectations(
        Path(environ.get(EXPECTED_PATH_VARIABLE, "").strip() or DEFAULT_EXPECTED_PATH)
    )
    min_chars = int(environ.get("SEXTANTE_PDF_MIN_CHARS_PER_PAGE", "") or DEFAULT_MIN_CHARS)
    return Path(samples), expectations, PdfInvoiceExtractor(min_chars), _entity(environ)


def _entity(environ: Mapping[str, str]) -> tuple[TargetEntity, EntityDenylist]:
    missing = [name for name in ENTITY_VARIABLES if not environ.get(name, "").strip()]
    if missing:
        raise GoldenSetError(f"{', '.join(missing)} not set. Expected the values of config/.env.")
    target = TargetEntity(
        environ["SEXTANTE_TARGET_ENTITY_NAME"].strip(),
        environ["SEXTANTE_TARGET_ENTITY_NIF"].strip(),
    )
    try:
        entries = read_entity_denylist(Path(environ["SEXTANTE_ENTITY_DENYLIST_PATH"].strip()))
    except DenylistFileError as error:
        raise GoldenSetError(f"SEXTANTE_ENTITY_DENYLIST_PATH: {error}") from None
    return target, EntityDenylist.of(entries)
