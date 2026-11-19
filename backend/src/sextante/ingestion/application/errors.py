"""Errors shared by the ingestion use cases."""

from sextante.platform.errors import DomainError


class InvoiceNotFoundError(DomainError):
    """No invoice has this identifier."""

    user_message_key = "errors.invoice.not_found"
