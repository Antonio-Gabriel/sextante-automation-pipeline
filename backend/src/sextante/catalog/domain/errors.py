"""Catalog errors. Messages name the sheet, the offending value and the expected form."""


class CatalogValidationError(ValueError):
    """Raised when the catalog content breaks a startup rule (REQ-MAP-012)."""


class CatalogFileError(ValueError):
    """Raised when the catalog file cannot be read as an xlsx workbook."""
