"""Traceability matrix (01-requisitos.md §0, 04-padroes-de-codigo.md §3.4).

Reads every @pytest.mark.requirement(...) in tests/ and checks it against the identifiers
declared in docs/. Fails when a test cites an identifier that does not exist. With
--strict, also fails when a REQ- or NFR- requirement has no test, which is the rule once
every ticket of the spec is delivered.

Usage:
    python scripts/traceability_matrix.py [--strict]
"""

import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Final

BACKEND: Final = Path(__file__).resolve().parents[1]
DOCS: Final = BACKEND.parent / "docs"
MARKER: Final = re.compile(r"@pytest\.mark\.requirement\(([^)]*)\)")
QUOTED_ID: Final = re.compile(r"\"([^\"]+)\"")
REQUIREMENT_HEADING: Final = re.compile(r"^### ((?:REQ|NFR)-[A-Z]+-\d{3})", re.MULTILINE)
SECURITY_HEADING: Final = re.compile(r"^## \d+\. (SEC-\d{2})", re.MULTILINE)
DECISION_HEADING: Final = re.compile(r"^### (\d+\.\d+) ", re.MULTILINE)
GAP_HEADING: Final = re.compile(r"^### (L-\d{2}) ", re.MULTILINE)
STATEMENT_RULE: Final = re.compile(r"^\| (R\d+) \|", re.MULTILINE)


def declared_requirements() -> set[str]:
    """Return the REQ- and NFR- identifiers declared in 01-requisitos.md.

    Example:
        "REQ-MAP-012" in declared_requirements()  # True
    """
    return set(REQUIREMENT_HEADING.findall((DOCS / "01-requisitos.md").read_text()))


def declared_identifiers() -> set[str]:
    """Return every identifier a test may cite: REQ, NFR, SEC, D, L and R.

    Example:
        {"SEC-15", "D-3.9", "L-07", "R4"} <= declared_identifiers()  # True
    """
    decisions = (DOCS / "00-decisoes-e-lacunas.md").read_text()
    security = (DOCS / "03-seguranca.md").read_text()
    return (
        declared_requirements()
        | set(SECURITY_HEADING.findall(security))
        | {f"D-{number}" for number in DECISION_HEADING.findall(decisions)}
        | set(GAP_HEADING.findall(decisions))
        | set(STATEMENT_RULE.findall(decisions))
    )


def cited_identifiers() -> dict[str, set[str]]:
    """Map each cited identifier to the test files that cite it.

    Example:
        cited_identifiers()["REQ-MAP-012"]  # {"tests/api/test_startup_catalog.py"}
    """
    citations: dict[str, set[str]] = defaultdict(set)
    for test_file in (BACKEND / "tests").rglob("test_*.py"):
        for identifier in _identifiers_in(test_file):
            citations[identifier].add(test_file.relative_to(BACKEND).as_posix())
    return citations


def _identifiers_in(test_file: Path) -> list[str]:
    return [
        identifier
        for arguments in MARKER.findall(test_file.read_text())
        for identifier in QUOTED_ID.findall(arguments)
    ]


def main(strict: bool) -> int:
    """Print the matrix and return the exit code.

    Example:
        sys.exit(main(strict=False))
    """
    citations = cited_identifiers()
    unknown = sorted(set(citations) - declared_identifiers())
    uncovered = sorted(declared_requirements() - set(citations))
    for identifier in sorted(citations):
        print(f"{identifier:<14} {', '.join(sorted(citations[identifier]))}")
    print(
        f"\nRequirements covered: {len(declared_requirements()) - len(uncovered)}"
        f" of {len(declared_requirements())}"
    )
    if unknown:
        print(f"Unknown identifiers cited by tests: {', '.join(unknown)}")
    if strict and uncovered:
        print(f"Requirements without a test: {', '.join(uncovered)}")
    return 1 if unknown or (strict and uncovered) else 0


if __name__ == "__main__":
    sys.exit(main(strict="--strict" in sys.argv[1:]))
