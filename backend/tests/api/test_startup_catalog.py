"""Catalog validation at startup (REQ-MAP-012): an invalid catalog never reaches coding."""

import json
from pathlib import Path
from typing import Final

import pytest

from sextante.main import create_app
from sextante.platform.limits import MAX_SHEET_ITEMS
from sextante.platform.settings import StartupConfigurationError
from tests.fixtures.synthetic_catalog import DEFAULT_OUTLAYS, DEFAULT_OUTLAYSP, SyntheticCatalog

OVERSIZED_OUTLAYS: Final = tuple(
    (f"O{n:05d}", f"Item {n}", f"Item {n}") for n in range(MAX_SHEET_ITEMS + 1)
)

INVALID_CATALOGS: Final = {
    "missing OUTLAYS sheet": (SyntheticCatalog(sheet_names=("OUTLAYSP",)), ("OUTLAYS", "missing")),
    "missing OUTLAYSP sheet": (SyntheticCatalog(sheet_names=("OUTLAYS",)), ("OUTLAYSP", "missing")),
    "column A is not No.": (
        SyntheticCatalog(header=("Code", "Description", "Description 2")),
        ("OUTLAYS", "column A"),
    ),
    "column C is not Description 2": (
        SyntheticCatalog(header=("No.", "Description", "Type")),
        ("OUTLAYS", "column C"),
    ),
    "empty item number": (
        SyntheticCatalog(outlays=(*DEFAULT_OUTLAYS, (None, "Sem código", "No code"))),
        ("OUTLAYS", "empty item number", "row 9"),
    ),
    "duplicate item number": (
        SyntheticCatalog(outlaysp=(*DEFAULT_OUTLAYSP, ("O00031", "Repetido", "Duplicate"))),
        ("OUTLAYSP", "duplicate item number", "O00031"),
    ),
    "O00999 missing": (
        SyntheticCatalog(outlaysp=DEFAULT_OUTLAYSP[:-1]),
        ("OUTLAYSP", "O00999"),
    ),
    "sheet above the model list limit": (
        SyntheticCatalog(outlays=OVERSIZED_OUTLAYS),
        ("OUTLAYS", f"{MAX_SHEET_ITEMS + 1} items", f"limit of {MAX_SHEET_ITEMS}"),
    ),
}


@pytest.mark.requirement("REQ-MAP-012")
@pytest.mark.parametrize("case", INVALID_CATALOGS, ids=list(INVALID_CATALOGS))
def test_application_refuses_to_start_with_invalid_catalog(
    case: str, valid_environment: dict[str, str], tmp_path: Path
) -> None:
    """The refusal names the sheet and the violated condition."""
    catalog, expected_fragments = INVALID_CATALOGS[case]
    valid_environment["SEXTANTE_CATALOG_PATH"] = str(catalog.write(tmp_path / "bad.xlsx"))

    with pytest.raises(StartupConfigurationError) as refusal:
        create_app(valid_environment)

    for fragment in expected_fragments:
        assert fragment in str(refusal.value)


@pytest.mark.requirement("REQ-MAP-012", "REQ-PLT-007")
def test_application_refuses_to_start_when_catalog_file_does_not_exist(
    valid_environment: dict[str, str], tmp_path: Path
) -> None:
    """A wrong catalog path is a configuration error, reported as such."""
    valid_environment["SEXTANTE_CATALOG_PATH"] = str(tmp_path / "absent.xlsx")

    with pytest.raises(StartupConfigurationError) as refusal:
        create_app(valid_environment)

    assert "SEXTANTE_CATALOG_PATH" in str(refusal.value)


@pytest.mark.requirement("REQ-MAP-012")
def test_application_refuses_to_start_when_catalog_is_not_a_workbook(
    valid_environment: dict[str, str], tmp_path: Path
) -> None:
    """A file that is not an xlsx workbook is refused, whatever its extension says."""
    impostor = tmp_path / "catalog.xlsx"
    impostor.write_text("not a workbook")
    valid_environment["SEXTANTE_CATALOG_PATH"] = str(impostor)

    with pytest.raises(StartupConfigurationError) as refusal:
        create_app(valid_environment)

    assert "not a valid xlsx workbook" in str(refusal.value)


@pytest.mark.requirement("REQ-MAP-012", "D-3.9")
def test_catalog_quirks_warn_without_refusing_startup(
    valid_environment: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    """Invisible characters and a missing English description are reported, not fatal."""
    create_app(valid_environment)

    warnings = {
        (record["item_number"], record["warning_kind"])
        for record in _json_records(capsys.readouterr().out)
        if record["event"] == "catalog_item_warning"
    }
    assert warnings == {
        ("O00060", "invisible_characters"),
        ("O00010", "invisible_characters"),
        ("O00061", "missing_english_description"),
    }


@pytest.mark.requirement("REQ-MAP-012", "SEC-15")
def test_catalog_warnings_identify_the_item_without_its_description(
    valid_environment: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    """The warning carries the item number, never the description text."""
    create_app(valid_environment)

    logged_text = capsys.readouterr().out
    assert "Ppassage" not in logged_text
    assert "desratização" not in logged_text


@pytest.mark.requirement("REQ-MAP-012", "D-3.9")
def test_non_breaking_space_at_the_end_of_a_description_still_warns(
    valid_environment: dict[str, str], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The invisible-character check runs on the raw cell, before trimming hides it."""
    catalog = SyntheticCatalog(outlays=(("O00070", "Taxa\xa0", "Fee"),))
    valid_environment["SEXTANTE_CATALOG_PATH"] = str(catalog.write(tmp_path / "nbsp.xlsx"))
    # This minimal catalog has no O00052, the default generic item.
    valid_environment["SEXTANTE_GENERIC_ITEMS"] = "O00070"

    create_app(valid_environment)

    assert '"item_number": "O00070", "warning_kind": "invisible_characters"' in (
        capsys.readouterr().out
    )


def _json_records(output: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in output.splitlines() if line.strip()]
