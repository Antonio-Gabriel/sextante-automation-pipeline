"""Port of the export use case: turning rows into a downloadable file (REQ-EXP-002)."""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from sextante.export.domain.export_rows import ExportRow


class ExportFormat(StrEnum):
    """Export file formats (REQ-EXP-002)."""

    CSV = "csv"
    XLSX = "xlsx"


@dataclass(frozen=True, slots=True)
class ExportFile:
    """A written export: its bytes and how to serve them."""

    content: bytes
    media_type: str
    extension: str


class SpreadsheetWriter(Protocol):
    """Port: write export rows in one format."""

    def write(self, rows: Sequence[ExportRow], export_format: ExportFormat) -> ExportFile:
        """Return the file for these rows, every cell neutralized (SEC-17)."""
        ...
