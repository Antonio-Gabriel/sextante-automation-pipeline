"""Catalog domain errors. Messages name the sheet, the offending value and the expected form."""

from sextante.platform.errors import DomainError


class CatalogValidationError(DomainError):
    """Raised when the catalog content breaks a startup rule (REQ-MAP-012)."""

    user_message_key = "errors.catalog.invalid"
