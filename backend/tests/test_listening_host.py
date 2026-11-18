"""Guard for L-07: without authentication, the server listens on 127.0.0.1 only."""

from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
REPOSITORY = BACKEND.parent
# Built from parts so that the literal never appears in the repository (L-07).
ALL_INTERFACES = ".".join(["0"] * 4)


@pytest.mark.requirement("SEC-06", "L-07")
def test_run_command_binds_to_localhost_only() -> None:
    """The documented run command listens on 127.0.0.1 and never on all interfaces."""
    makefile = (BACKEND / "Makefile").read_text()

    assert "--host 127.0.0.1" in makefile
    assert ALL_INTERFACES not in makefile


@pytest.mark.requirement("SEC-06", "L-07")
def test_no_source_or_config_file_listens_on_all_interfaces() -> None:
    """The all-interfaces address appears nowhere in code or configuration while L-07 is open."""
    candidates = [*BACKEND.joinpath("src").rglob("*.py"), *REPOSITORY.joinpath("config").rglob("*")]

    offenders = [
        str(path) for path in candidates if path.is_file() and ALL_INTERFACES in path.read_text()
    ]

    assert offenders == []
