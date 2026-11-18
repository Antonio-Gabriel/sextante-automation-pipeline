"""Load the catalog once at startup (NFR-PRF-003) and report its warnings."""

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from sextante.catalog.domain.catalog_builder import BuiltCatalog, RawCatalogSheet, build_catalog
from sextante.catalog.domain.model import CatalogDigest
from sextante.platform.errors import DomainError

logger = logging.getLogger(__name__)


class CatalogFileError(DomainError):
    """Raised by a CatalogWorkbookReader when the file is missing or not a workbook."""

    user_message_key = "errors.catalog.unreadable"


class CatalogWorkbookReader(Protocol):
    """Port: reads the catalog file as raw sheets and digests its content."""

    def read_sheets(self, path: Path) -> Mapping[str, RawCatalogSheet]:
        """Return every worksheet as raw rows. Raises CatalogFileError when unreadable."""
        ...

    def digest(self, path: Path) -> CatalogDigest:
        """Return the SHA-256 of the file content."""
        ...


def load_catalog(path: Path, reader: CatalogWorkbookReader) -> BuiltCatalog:
    """Read, validate and build the catalog, logging one warning per catalog quirk.

    Example:
        catalog = load_catalog(settings.catalog_path, XlsxCatalogWorkbookReader()).catalog

    Raises:
        CatalogFileError: when the file is missing or not a workbook.
        CatalogValidationError: when the content breaks a startup rule.
    """
    built = build_catalog(reader.read_sheets(path), reader.digest(path))
    for warning in built.warnings:
        # Item number and sheet identify the row; the description text is left out.
        logger.warning(
            "catalog_item_warning",
            extra={
                "sheet": warning.sheet.value,
                "item_number": warning.item_number.value,
                "warning_kind": warning.kind.value,
            },
        )
    return built
