"""Golden set: the deterministic steps measured on the sample invoices (NFR-TST-001, D-3.18).

Run with ``make golden``, which is ``python -m tests.golden.runner`` from backend/.

Measures extraction, entity, target sheet, line types and refusals, without calling the
model. The samples are read from a local folder and never enter the repository; the
report names samples, fields and closed-set values only, never text from a sample.

Expected results are a proposal until AMT confirms them (L-02), so no accuracy figure
is published from this report.
"""

import os
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from sextante.ingestion.domain.line_type import classify_line_type
from sextante.ingestion.domain.model import (
    ExtractedInvoice,
    ExtractionRejection,
    FileFormat,
    missing_fields,
)
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
from sextante.platform.settings import PDF_MIN_CHARS_DEFAULT, PDF_MIN_CHARS_MAXIMUM

SAMPLES_PATH_VARIABLE: Final = "SEXTANTE_GOLDEN_SAMPLES_PATH"
EXPECTED_PATH_VARIABLE: Final = "SEXTANTE_GOLDEN_EXPECTED_PATH"
DEFAULT_EXPECTED_PATH: Final = Path(__file__).resolve().parent / "expected_results.yaml"


class GoldenSetError(RuntimeError):
    """The golden set cannot run: missing folder, or an unreadable expected-results file."""


@dataclass(frozen=True, slots=True)
class EntityReference:
    """The target entity and the denylist the entity check runs against."""

    target: TargetEntity
    denylist: EntityDenylist


class GoldenSettings(BaseModel):
    """The SEXTANTE_ variables the golden set reads, validated like the application's."""

    model_config = ConfigDict(frozen=True, extra="ignore", str_strip_whitespace=True)

    samples_path: Path
    expected_path: Path = DEFAULT_EXPECTED_PATH
    target_entity_name: str = Field(min_length=1)
    target_entity_nif: str = Field(min_length=1)
    entity_denylist_path: Path
    pdf_min_chars_per_page: int = Field(
        default=PDF_MIN_CHARS_DEFAULT, ge=1, le=PDF_MIN_CHARS_MAXIMUM
    )

    @classmethod
    def from_environment(cls, environ: Mapping[str, str]) -> Self:
        """Read the variables; a missing or invalid one is named in the error.

        Example:
            GoldenSettings.from_environment(os.environ).samples_path

        Raises:
            GoldenSetError: naming each missing or invalid variable.
        """
        if not environ.get(SAMPLES_PATH_VARIABLE, "").strip():
            raise GoldenSetError(
                f"{SAMPLES_PATH_VARIABLE} is not set. Expected the local folder with the "
                "sample invoices, which never enter the repository."
            )
        values = {
            name.removeprefix("SEXTANTE_GOLDEN_").removeprefix("SEXTANTE_").lower(): value
            for name, value in environ.items()
            if name.startswith("SEXTANTE_") and value.strip()
        }
        try:
            return cls.model_validate(values)
        except ValidationError as error:
            names = ", ".join(_variable_name(e["loc"]) for e in error.errors())
            raise GoldenSetError(
                f"Invalid or missing {names}. Expected the values described in config/.env.example."
            ) from None


def _variable_name(location: tuple[int | str, ...]) -> str:
    field = str(location[0]) if location else "?"
    prefix = "SEXTANTE_GOLDEN_" if field in {"samples_path", "expected_path"} else "SEXTANTE_"
    return prefix + field.upper()


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
    # Field names the extraction is expected not to find, never their values.
    missing_fields: tuple[str, ...] = ()


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
        load_expectations(DEFAULT_EXPECTED_PATH).samples[0].id  # "INV-001"

    Raises:
        GoldenSetError: when the file is missing or does not match the schema.
    """
    try:
        return GoldenExpectations.model_validate(yaml.safe_load(path.read_text("utf-8")))
    except (OSError, yaml.YAMLError, ValidationError) as error:
        raise GoldenSetError(
            f"Expected results {path} are unreadable ({type(error).__name__}). "
            "Expected the format of tests/golden/expected_results.yaml."
        ) from None


def run_golden(
    samples_dir: Path,
    expectations: GoldenExpectations,
    extractor: InvoiceExtractor,
    entity: EntityReference,
) -> list[SampleResult]:
    """Measure every expected sample found in the folder.

    Example:
        results = run_golden(Path("/samples"), expectations, extractor, entity)

    Raises:
        GoldenSetError: when the folder does not exist.
    """
    if not samples_dir.is_dir():
        raise GoldenSetError(f"Samples folder {samples_dir} does not exist. Expected a folder.")
    results = []
    for expectation in expectations.samples:
        sample = sample_file(samples_dir, expectation.id)
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


def sample_file(samples_dir: Path, sample_id: str) -> Path | None:
    """The sample's PDF in the folder, named after its identifier, or None.

    Example:
        sample_file(Path("/samples"), "INV-001")  # Path("/samples/INV-001_x.pdf")
    """
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
    entity: EntityReference,
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
    entity: EntityReference,
) -> list[str]:
    verdict = check_billed_entity(extraction.billed_entities, entity.target, entity.denylist)
    sheet = target_sheet_for(verdict.verdict)
    got: Mapping[str, object] = {
        "entity": verdict.verdict.value,
        "target_sheet": sheet.value if sheet else None,
        "line count": len(extraction.lines),
        "line types": [classify_line_type(line.description).value for line in extraction.lines],
        "missing fields": list(missing_fields(extraction)),
    }
    expected: Mapping[str, object] = {
        "entity": expectation.entity,
        "target_sheet": expectation.target_sheet,
        "line count": len(expectation.lines),
        "line types": [line.line_type for line in expectation.lines],
        "missing fields": list(expectation.missing_fields),
    }
    return [
        _differs(name, expected[name], got[name]) for name in got if got[name] != expected[name]
    ]


def _differs(field: str, expected: object, got: object) -> str:
    return f"{field}: expected {expected}, got {got}"


def golden_main(environ: Mapping[str, str], write: Callable[[str], None]) -> int:
    """Run the golden set from SEXTANTE_ variables; 0 when every sample matches.

    Returns 2, with a clear message, when a variable is missing or invalid or a file
    cannot be read; 1 when a sample diverges.

    Example:
        sys.exit(golden_main(os.environ, print))
    """
    try:
        settings = GoldenSettings.from_environment(environ)
        expectations = load_expectations(settings.expected_path)
        extractor = PdfInvoiceExtractor(settings.pdf_min_chars_per_page)
        results = run_golden(
            settings.samples_path, expectations, extractor, entity_reference(settings)
        )
    except GoldenSetError as error:
        write(str(error))
        return 2
    for line in report_lines(results):
        write(line)
    if expectations.proposal:
        write("Expected results are a proposal still to be confirmed by AMT (L-02).")
    return 1 if any(result.divergences for result in results) else 0


def entity_reference(settings: GoldenSettings) -> EntityReference:
    """The target entity and denylist the check runs against, from the settings.

    Example:
        entity_reference(settings).target.name

    Raises:
        GoldenSetError: when the denylist file cannot be read.
    """
    try:
        entries = read_entity_denylist(settings.entity_denylist_path)
    except DenylistFileError as error:
        raise GoldenSetError(f"SEXTANTE_ENTITY_DENYLIST_PATH: {error}") from None
    target = TargetEntity(settings.target_entity_name, settings.target_entity_nif)
    return EntityReference(target, EntityDenylist.of(entries))


if __name__ == "__main__":
    sys.exit(golden_main(os.environ, print))
