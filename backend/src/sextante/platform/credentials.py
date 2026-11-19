"""Credentials of every /api call but the health check (SEC-06, L-07).

Two credentials open the API, both compared in the server:
- the key of programs, ``X-API-Key``, compared by digest in constant time with SEXTANTE_API_KEY;
- the session of a person, an HttpOnly cookie opened by the access token (session.py).

Both stand for one principal: they close the API to whoever holds neither, but do not
tell people apart. The author of a review is still SEXTANTE_REVIEWER_ID.
"""

import logging
from typing import Annotated, Final

from fastapi import Request, Security
from fastapi.security import APIKeyCookie, APIKeyHeader

from sextante.platform.errors import DomainError
from sextante.platform.session import SESSION_COOKIE, SessionStore, secret_matches

logger = logging.getLogger(__name__)

API_KEY_HEADER: Final = "X-API-Key"
# The one principal behind both credentials (L-07): it identifies the caller of the
# rate limits, so a browser and a script share one quota.
PRINCIPAL: Final = "operator"

# auto_error is off so the refusal goes through the domain error handler: the same
# Portuguese body, with a correlation id, as every other error (REQ-PLT-005).
_api_key_scheme = APIKeyHeader(
    name=API_KEY_HEADER,
    auto_error=False,
    description="The key set in SEXTANTE_API_KEY, for programs. Or the session cookie.",
)
_session_scheme = APIKeyCookie(
    name=SESSION_COOKIE,
    auto_error=False,
    description="The session opened by POST /api/session with the access token, for people.",
)


class CredentialInvalidError(DomainError):
    """The request carried neither the configured key nor an open session."""

    user_message_key = "errors.auth.credential_invalid"


async def require_credential(
    request: Request,
    key: Annotated[str | None, Security(_api_key_scheme)] = None,
    session_id: Annotated[str | None, Security(_session_scheme)] = None,
) -> None:
    """Refuse the request unless it carries the configured key or an open session.

    Example:
        app.include_router(router, dependencies=[Depends(require_credential)])

    Raises:
        CredentialInvalidError: when both are missing or wrong.
    """
    sessions: SessionStore = request.app.state.sessions
    if not (secret_matches(key, request.app.state.api_key) or sessions.is_open(session_id)):
        # The event and the path only: never the key or session that was sent (SEC-15).
        logger.warning("credential_rejected", extra={"path": request.url.path})
        raise CredentialInvalidError("Missing or wrong credential. Expected the key or a session.")
    request.state.principal = PRINCIPAL
