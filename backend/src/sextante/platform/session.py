"""Sessions of people, opened by the access token (SEC-06, L-07).

A person types the access token once; the server compares it with SEXTANTE_ACCESS_TOKEN
in constant time and answers with a session cookie the page cannot read: HttpOnly,
SameSite=Strict, Secure by default, of limited life. The browser never holds the API key.

Known limitations of this version, declared rather than hidden:
- sessions live in this process's memory: a restart ends them, and two instances do not
  share them (the same limit as the rate counters of SEC-12);
- one token for everyone, like the key: a session does not tell people apart.
"""

import hashlib
import hmac
import logging
import secrets
from dataclasses import dataclass
from typing import Annotated, Final, Literal

from fastapi import APIRouter, Cookie, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from sextante.platform.errors import DomainError
from sextante.platform.rate_limit import Monotonic, enforce_rate_limits
from sextante.platform.settings import SETTING_TEXT_MAX_LENGTH

logger = logging.getLogger(__name__)

SESSION_COOKIE: Final = "sextante_session"
# The cookie goes to the API only: the pages of the frontend never carry it.
SESSION_COOKIE_PATH: Final = "/api"
SESSION_ID_BYTES: Final = 32

session_router = APIRouter(prefix="/api/session", tags=["session"])
session_status_router = APIRouter(prefix="/api/session", tags=["session"])


class AccessTokenInvalidError(DomainError):
    """The access token sent to open a session is not the configured one."""

    user_message_key = "errors.auth.access_token_invalid"


class SessionStore:
    """Open sessions in this process's memory, each with an absolute expiry.

    Only the digest of a session id is kept, so the memory holds nothing a browser sends.

    Example:
        store = SessionStore(8 * 3600, time.monotonic)
        session_id = store.open()
    """

    def __init__(self, lifetime_seconds: float, monotonic: Monotonic) -> None:
        self.lifetime_seconds = lifetime_seconds
        self._monotonic = monotonic
        self._expiry: dict[str, float] = {}

    def open(self) -> str:
        """Open a session and return its id, dropping the sessions already expired."""
        now = self._monotonic()
        self._expiry = {digest: end for digest, end in self._expiry.items() if end > now}
        session_id = secrets.token_urlsafe(SESSION_ID_BYTES)
        self._expiry[_digest(session_id)] = now + self.lifetime_seconds
        return session_id

    def is_open(self, session_id: str | None) -> bool:
        """Whether this id names a session not yet ended nor expired."""
        end = self._expiry.get(_digest(session_id)) if session_id else None
        return end is not None and self._monotonic() < end

    def close(self, session_id: str | None) -> None:
        """End the session, if there is one."""
        if session_id:
            self._expiry.pop(_digest(session_id), None)


@dataclass(frozen=True, slots=True)
class SessionPolicy:
    """What opens a session, and the cookie that carries it."""

    access_token: SecretStr
    secure_cookie: bool


class AccessTokenRequest(BaseModel):
    """Input contract of the login (SEC-08: unknown fields refused)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    token: str = Field(max_length=SETTING_TEXT_MAX_LENGTH)


class SessionResponse(BaseModel):
    """Output contract of the session check: answered only to an open credential."""

    model_config = ConfigDict(frozen=True)

    authenticated: Literal[True]


SessionCookie = Annotated[str | None, Cookie(alias=SESSION_COOKIE, include_in_schema=False)]


@session_router.post("", status_code=204, dependencies=[Depends(enforce_rate_limits)])
async def open_session_route(
    body: AccessTokenRequest, request: Request, response: Response
) -> None:
    """Open a session when the access token is the configured one.

    Example:
        POST /api/session {"token": "..."} -> 204, Set-Cookie: sextante_session=...

    Raises:
        AccessTokenInvalidError: when the token is wrong; no cookie is set.
    """
    policy: SessionPolicy = request.app.state.session_policy
    expected = policy.access_token.get_secret_value().encode()
    if not hmac.compare_digest(body.token.encode(), expected):
        # The event only: never the token that was sent (SEC-15).
        logger.warning("access_token_rejected")
        raise AccessTokenInvalidError("Wrong access token. Expected SEXTANTE_ACCESS_TOKEN.")
    store: SessionStore = request.app.state.sessions
    response.set_cookie(
        SESSION_COOKIE,
        store.open(),
        max_age=int(store.lifetime_seconds),
        path=SESSION_COOKIE_PATH,
        secure=policy.secure_cookie,
        httponly=True,
        samesite="strict",
    )
    logger.info("session_opened")


@session_router.post("/end", status_code=204)
async def end_session_route(
    request: Request, response: Response, session_id: SessionCookie = None
) -> None:
    """End the session of this browser, and clear its cookie. Ending none is no error.

    Example:
        POST /api/session/end -> 204, Set-Cookie: sextante_session=""; Max-Age=0
    """
    store: SessionStore = request.app.state.sessions
    store.close(session_id)
    policy: SessionPolicy = request.app.state.session_policy
    response.delete_cookie(
        SESSION_COOKIE,
        path=SESSION_COOKIE_PATH,
        secure=policy.secure_cookie,
        httponly=True,
        samesite="strict",
    )
    logger.info("session_ended")


@session_status_router.get("")
async def read_session_route() -> SessionResponse:
    """Answer when the request carries an open credential; the guard refuses the others.

    Example:
        GET /api/session -> {"authenticated": true}, or 401
    """
    return SessionResponse(authenticated=True)


def _digest(session_id: str) -> str:
    return hashlib.sha256(session_id.encode()).hexdigest()
