"""Every domain error points at a Portuguese text that exists (REQ-PLT-006)."""

import pytest

from sextante.catalog.application.load_catalog import CatalogFileError
from sextante.catalog.domain.errors import CatalogValidationError
from sextante.platform.errors import DomainError
from sextante.platform.user_messages import USER_MESSAGES_PT


@pytest.mark.requirement("REQ-PLT-006")
@pytest.mark.parametrize("error_type", [DomainError, CatalogValidationError, CatalogFileError])
def test_every_domain_error_has_a_portuguese_user_message(error_type: type[DomainError]) -> None:
    """A user_message_key without text would surface as a raw key on the screen."""
    assert error_type.user_message_key in USER_MESSAGES_PT
