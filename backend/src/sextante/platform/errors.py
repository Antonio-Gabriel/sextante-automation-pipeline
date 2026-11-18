"""Base class of domain errors (04-padroes-de-codigo.md §1.6)."""

from typing import ClassVar


class DomainError(Exception):
    """A business rule refused an operation. The message is English, for logs and developers.

    ``user_message_key`` points at the Portuguese text shown to the user (REQ-PLT-006).

    Example:
        class CatalogValidationError(DomainError):
            user_message_key = "errors.catalog.invalid"
    """

    user_message_key: ClassVar[str] = "errors.internal"
