"""Rate limits per endpoint, 429 with Retry-After (SEC-12, SEC-19).

Fixed windows counted in this process's memory. With one process that is enough; with
two instances each one allows the full quota, which is the known limitation of this
version (SEC-12): production needs a shared counter, 00-decisoes-e-lacunas.md §6.
"""

import hashlib
import logging
import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Final

from fastapi import Request

from sextante.platform.api_key import API_KEY_HEADER
from sextante.platform.errors import DomainError

logger = logging.getLogger(__name__)

MINUTE: Final = 60.0
HOUR: Final = 3600.0
GENERAL_RULE: Final = "general"

Monotonic = Callable[[], float]


@dataclass(frozen=True, slots=True)
class RateLimit:
    """At most ``requests`` per ``window_seconds`` for one caller."""

    requests: int
    window_seconds: float


class RateLimitExceededError(DomainError):
    """The caller went over a limit; ``retry_after`` says how many seconds to wait."""

    user_message_key = "errors.rate_limit.exceeded"

    def __init__(self, message: str, retry_after: int) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class RateLimiter:
    """Count requests per rule and caller in fixed windows of a monotonic clock.

    Example:
        limiter = RateLimiter(limits, time.monotonic)
        limiter.check("upload", caller)  # raises RateLimitExceededError over the limit
    """

    def __init__(self, limits: Mapping[str, RateLimit], monotonic: Monotonic) -> None:
        self._limits = limits
        self._monotonic = monotonic
        self._counts: dict[tuple[str, str, int], int] = {}

    def check(self, rule: str, caller: str) -> None:
        """Count one request against the rule; refuse it when the window is full.

        Example:
            limiter.check(GENERAL_RULE, "a1b2c3")

        Raises:
            RateLimitExceededError: with the seconds until the window opens again.
        """
        limit = self._limits[rule]
        now = self._monotonic()
        window = int(now // limit.window_seconds)
        key = (rule, caller, window)
        if self._counts.get(key, 0) >= limit.requests:
            retry_after = max(1, math.ceil((window + 1) * limit.window_seconds - now))
            raise RateLimitExceededError(
                f"Rate limit {rule} of {limit.requests} per {limit.window_seconds:g}s reached. "
                f"Expected a retry after {retry_after}s.",
                retry_after,
            )
        self._forget_closed_windows(window, rule)
        self._counts[key] = self._counts.get(key, 0) + 1

    def _forget_closed_windows(self, window: int, rule: str) -> None:
        # Only the current window of a rule matters; older counts would only grow memory.
        for stale in [k for k in self._counts if k[0] == rule and k[2] < window]:
            del self._counts[stale]


# Endpoints with their own, tighter limit (SEC-12), by method and route template.
COSTLY_ROUTES: Final = {
    ("POST", "/api/invoices"): "upload",
    ("POST", "/api/invoices/{invoice_id}/reprocess"): "reprocess",
    ("GET", "/api/exports/{job_id}"): "export",
    ("PATCH", "/api/encoded-lines/{encoded_line_id}"): "correction",
}


async def enforce_rate_limits(request: Request) -> None:
    """Count the request against the general limit and its endpoint's own limit.

    Runs after the key check, so a refused credential never uses anyone's quota.

    Example:
        app.include_router(router, dependencies=[Depends(enforce_rate_limits)])

    Raises:
        RateLimitExceededError: when either limit is reached.
    """
    limiter: RateLimiter = request.app.state.rate_limiter
    caller = _caller(request)
    route = request.scope.get("route")
    rules = [GENERAL_RULE]
    costly = COSTLY_ROUTES.get((request.method, getattr(route, "path", "")))
    rules += [costly] if costly else []
    try:
        for rule in rules:
            limiter.check(rule, caller)
    except RateLimitExceededError as error:
        # The rule and the path only: never the key that identifies the caller (SEC-15).
        logger.warning("rate_limited", extra={"rule": rule, "path": request.url.path})
        raise error from None


def _caller(request: Request) -> str:
    # The key's digest is the identity while there is no per-person login; without a
    # key, the address it came from (SEC-12: "origem enquanto não houver identidade").
    key = request.headers.get(API_KEY_HEADER)
    if key:
        return hashlib.sha256(key.encode()).hexdigest()[:16]
    return request.client.host if request.client else "unknown"
