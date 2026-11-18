"""API key on every /api call but the health check (L-07, SEC-06).

One key, set in configuration, compared in constant time. It closes the API to
whoever does not hold it; it does not tell people apart: the author of a review is
still SEXTANTE_REVIEWER_ID.
"""

import hmac
import logging
from typing import Annotated, Final

from fastapi import Request, Security
from fastapi.security import APIKeyHeader
from pydantic import SecretStr

from sextante.platform.errors import DomainError

logger = logging.getLogger(__name__)

API_KEY_HEADER: Final = "X-API-Key"

# auto_error is off so the refusal goes through the domain error handler: the same
# Portuguese body, with a correlation id, as every other error (REQ-PLT-005).
_api_key_scheme = APIKeyHeader(
    name=API_KEY_HEADER,
    auto_error=False,
    description="The key set in SEXTANTE_API_KEY. Mandatory on every /api call but health.",
)


class ApiKeyInvalidError(DomainError):
    """The request carried no API key, or not the configured one."""

    user_message_key = "errors.auth.api_key_invalid"


async def require_api_key(
    request: Request, sent: Annotated[str | None, Security(_api_key_scheme)] = None
) -> None:
    """Refuse the request unless it carries the configured key.

    Example:
        app.include_router(router, dependencies=[Depends(require_api_key)])

    Raises:
        ApiKeyInvalidError: when the key is missing or wrong.
    """
    expected: SecretStr = request.app.state.api_key
    given = (sent or "").encode()
    if not hmac.compare_digest(given, expected.get_secret_value().encode()):
        # The event and the path only: never the key that was sent (SEC-15).
        logger.warning("api_key_rejected", extra={"path": request.url.path})
        raise ApiKeyInvalidError("Missing or wrong X-API-Key. Expected the configured key.")
