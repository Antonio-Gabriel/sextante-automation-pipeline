"""Ticket 13: the golden set runner, on a folder of SYNTHETIC samples (NFR-TST-001, D-3.18)."""

from pathlib import Path

import pytest
import yaml

from tests.fixtures.synthetic_pdf import (
    air_ticket_pdf,
    care_of_pdf,
    model_invoice_pdf,
    scanned_pdf,
)
from tests.golden.model_run import LineResult, TokenUsage, report
from tests.golden.runner import DEFAULT_EXPECTED_PATH, golden_main, load_expectations

CARE_OF_EXPECTATION: dict[str, object] = {
    "id": "SYN-002",
    "entity": "NO_MATCH",
    "target_sheet": "OUTLAYSP",
    "lines": [{"position": 1, "line_type": "service", "item_number": "O00031"}],
}
EXPECTATIONS: dict[str, object] = {
    "version": 1,
    "proposal": True,
    "samples": [
        {
            "id": "SYN-001",
            "entity": "MATCH",
            "target_sheet": "OUTLAYS",
            "lines": [{"position": 1, "line_type": "service", "item_number": "O00004"}],
        },
        CARE_OF_EXPECTATION,
        {"id": "SYN-003", "rejected": "pdf_without_text_layer"},
    ],
}


@pytest.fixture
def golden_environment(tmp_path: Path, valid_environment: dict[str, str]) -> dict[str, str]:
    samples = tmp_path / "samples"
    samples.mkdir()
    (samples / "SYN-001_air_synthetic.pdf").write_bytes(model_invoice_pdf(air_ticket_pdf()))
    (samples / "SYN-002_care_of_synthetic.pdf").write_bytes(model_invoice_pdf(care_of_pdf()))
    (samples / "SYN-003_scan_synthetic.pdf").write_bytes(scanned_pdf())
    expected = tmp_path / "expected.yaml"
    expected.write_text(yaml.safe_dump(EXPECTATIONS), encoding="utf-8")
    return {
        **valid_environment,
        "SEXTANTE_GOLDEN_SAMPLES_PATH": str(samples),
        "SEXTANTE_GOLDEN_EXPECTED_PATH": str(expected),
    }


def _run(environment: dict[str, str]) -> tuple[int, list[str]]:
    output: list[str] = []
    return golden_main(environment, output.append), output


@pytest.mark.requirement("NFR-TST-001", "D-3.18")
def test_samples_that_match_the_expected_results_pass(golden_environment: dict[str, str]) -> None:
    """Extraction, entity, sheet, line types and refusals all as expected: exit 0."""
    code, output = _run(golden_environment)

    assert code == 0
    assert output[:4] == ["SYN-001 ok", "SYN-002 ok", "SYN-003 ok", "3 samples, 0 with divergences"]


@pytest.mark.requirement("NFR-TST-001")
def test_a_divergence_fails_and_names_the_field(
    golden_environment: dict[str, str], tmp_path: Path
) -> None:
    """Expecting MATCH for a c/o invoice is a divergence on the entity and the sheet."""
    wrong = {**EXPECTATIONS, "samples": [{**CARE_OF_EXPECTATION, "entity": "MATCH"}]}
    (tmp_path / "expected.yaml").write_text(yaml.safe_dump(wrong), encoding="utf-8")

    code, output = _run(golden_environment)

    assert code == 1
    assert output[0] == "SYN-002 entity: expected MATCH, got NO_MATCH"


@pytest.mark.requirement("NFR-TST-001", "D-3.18")
def test_without_the_samples_folder_the_command_says_so(valid_environment: dict[str, str]) -> None:
    """No samples variable: a clear message and exit 2, never a silent pass."""
    code, output = _run(valid_environment)

    assert code == 2
    assert output == [
        "SEXTANTE_GOLDEN_SAMPLES_PATH is not set. Expected the local folder with the sample "
        "invoices, which never enter the repository."
    ]


@pytest.mark.requirement("SEC-15", "D-3.18")
def test_the_report_carries_no_text_from_a_sample(golden_environment: dict[str, str]) -> None:
    """Identifiers, field names and closed-set values only: no description, no name."""
    _, output = _run(golden_environment)
    report = "\n".join(output)

    for excerpt in ("Passagem", "Sobrestadia", "Operadora", "Synthetic", "SYN-2026"):
        assert excerpt not in report


@pytest.mark.requirement("NFR-TST-001", "D-3.18")
def test_the_repository_expected_results_name_lines_by_position_only() -> None:
    """The proposal has the twelve samples and no excerpt of any of them (D-3.18)."""
    expectations = load_expectations(DEFAULT_EXPECTED_PATH)
    raw = yaml.safe_load(DEFAULT_EXPECTED_PATH.read_text(encoding="utf-8"))
    line_keys = {
        key for sample in raw["samples"] for line in sample.get("lines", []) for key in line
    }

    assert [sample.id for sample in expectations.samples] == [f"INV-{n:03d}" for n in range(1, 13)]
    assert expectations.proposal is True
    assert line_keys == {"position", "line_type", "item_number"}


@pytest.mark.requirement("NFR-TST-001")
@pytest.mark.parametrize("value", ["many", "0"])
def test_an_invalid_minimum_of_text_is_named_not_a_traceback(
    golden_environment: dict[str, str], value: str
) -> None:
    """A non-number, or 0, which would switch off the scanned-PDF refusal: exit 2."""
    code, output = _run({**golden_environment, "SEXTANTE_PDF_MIN_CHARS_PER_PAGE": value})

    assert code == 2
    assert "SEXTANTE_PDF_MIN_CHARS_PER_PAGE" in output[0]


@pytest.mark.requirement("NFR-TST-001", "REQ-ING-003")
def test_a_field_extracted_or_missing_against_expectation_is_a_divergence(
    golden_environment: dict[str, str], tmp_path: Path
) -> None:
    """Extraction is measured on its fields too: by name, never by value."""
    expecting_no_date = {**CARE_OF_EXPECTATION, "missing_fields": ["invoice_date"]}
    wrong = {**EXPECTATIONS, "samples": [expecting_no_date]}
    (tmp_path / "expected.yaml").write_text(yaml.safe_dump(wrong), encoding="utf-8")

    code, output = _run(golden_environment)

    assert (code, output[0]) == (1, "SYN-002 missing fields: expected ['invoice_date'], got []")


@pytest.mark.requirement("NFR-TST-001", "SEC-15")
def test_the_model_run_report_holds_codes_and_confidence_only() -> None:
    """Hits, flagged lines and tokens, from item numbers: nothing a sample wrote."""
    results = [
        LineResult("INV-001", 1, "O00004", "O00004", "MEDIUM", False),
        LineResult("INV-008", 1, "O00999", None, None, True, "model unavailable"),
    ]

    lines = report(results, TokenUsage(1200, 80, 1900, 3800))

    assert lines == [
        "INV-001 line 1: expected O00004, assigned O00004, MEDIUM",
        "INV-008 line 1: expected O00999, assigned -, -, flagged (model unavailable)",
        "2 lines, 1 as expected, 1 flagged for review",
        "Tokens: 1200 in, 80 out, 1900 written to cache, 3800 read from cache",
        "Expected results are a proposal to be confirmed by AMT (L-02): not for publication.",
    ]
