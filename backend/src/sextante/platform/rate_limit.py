"""Rate limits per endpoint, 429 with Retry-After (SEC-12, SEC-19).

Fixed windows counted in this process's memory, per caller. Two limits apply to a
request: the general one, and its endpoint's own when the endpoint is costly. A request
is counted only when every limit lets it through, so a refusal uses no quota.

Known limitations of this version, declared rather than hidden:
- the counters live in one process: with two instances each allows the full quota
  (SEC-12); production needs a shared counter, 00-decisoes-e-lacunas.md §6;
- a fixed window lets up to twice the quota through across a window boundary;
- the caller is the API key, and there is one key (L-07): everyone shares one quota.
"""

import hashlib
import logging
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from fastapi import Request

from sextante.platform.api_key import API_KEY_HEADER
from sextante.platform.errors import DomainError

logger = logging.getLogger(__name__)

MINUTE: Final = 60.0
HOUR: Final = 3600.0

Monotonic = Callable[[], float]


class RateRule(StrEnum):
    """The closed set of limits of SEC-12."""

    GENERAL = "general"
    UPLOAD = "upload"
    REPROCESS = "reprocess"
    EXPORT = "export"
    CORRECTION = "correction"


@dataclass(frozen=True, slots=True)
class RateLimit:
    """At most ``requests`` per fixed window of ``window_seconds``, on a monotonic clock."""

    requests: int
    window_seconds: float

    def window_at(self, now: float) -> int:
        """The number of the fixed window that holds ``now``.

        Example:
            RateLimit(10, 60.0).window_at(1000.0)  # 16
        """
        return int(now // self.window_seconds)

    def seconds_left(self, now: float) -> float:
        """Seconds from ``now`` to the end of its window.

        Example:
            RateLimit(10, 60.0).seconds_left(1000.0)  # 20.0
        """
        return (self.window_at(now) + 1) * self.window_seconds - now


class RateLimitExceededError(DomainError):
    """The caller went over a limit; ``retry_after`` says how many seconds to wait."""

    user_message_key = "errors.rate_limit.exceeded"

    def __init__(self, rule: RateRule, retry_after: int) -> None:
        super().__init__(f"Rate limit {rule.value} reached. Expected a retry after {retry_after}s.")
        self.rule = rule
        self.retry_after = retry_after

    def response_headers(self) -> Mapping[str, str]:
        """When to come back, in seconds (SEC-12).

        Example:
            error.response_headers()  # {"Retry-After": "20"}
        """
        return {"Retry-After": str(self.retry_after)}


class RateLimiter:
    """Count requests per rule and caller, in fixed windows of a monotonic clock.

    Memory is one counter per rule and caller: a new window replaces the old count.

    Example:
        limiter = RateLimiter(limits, time.monotonic)
        limiter.check((RateRule.GENERAL, RateRule.UPLOAD), caller)
    """

    def __init__(self, limits: Mapping[RateRule, RateLimit], monotonic: Monotonic) -> None:
        self._limits = limits
        self._monotonic = monotonic
        self._counts: dict[tuple[RateRule, str], tuple[int, int]] = {}

    def check(self, rules: Sequence[RateRule], caller: str) -> None:
        """Let the request through every rule and count it, or refuse it and count nothing.

        Example:
            limiter.check((RateRule.GENERAL,), "a1b2c3")

        Raises:
            RateLimitExceededError: naming the first full rule and the seconds to wait.
        """
        now = self._monotonic()
        windows = {rule: self._limits[rule].window_at(now) for rule in rules}
        for rule in rules:
            limit = self._limits[rule]
            if self._used(rule, caller, windows[rule]) >= limit.requests:
                raise RateLimitExceededError(rule, max(1, math.ceil(limit.seconds_left(now))))
        for rule in rules:
            used = self._used(rule, caller, windows[rule])
            self._counts[(rule, caller)] = (windows[rule], used + 1)

    def _used(self, rule: RateRule, caller: str, window: int) -> int:
        counted_window, used = self._counts.get((rule, caller), (window, 0))
        return used if counted_window == window else 0


async def enforce_rate_limits(request: Request) -> None:
    """Count the request against the general limit and its endpoint's own limit.

    Runs after the key check, so a refused credential never uses anyone's quota. The
    costly endpoints are named by their route function, in the composition root.

    Example:
        app.include_router(router, dependencies=[Depends(enforce_rate_limits)])

    Raises:
        RateLimitExceededError: when either limit is reached.
    """
    limiter: RateLimiter = request.app.state.rate_limiter
    costly: Mapping[object, RateRule] = request.app.state.costly_endpoints
    endpoint_rule = costly.get(request.scope.get("endpoint"))
    rules = (RateRule.GENERAL, endpoint_rule) if endpoint_rule else (RateRule.GENERAL,)
    try:
        limiter.check(rules, _caller(request))
    except RateLimitExceededError as error:
        # The rule and the path only: never the key that identifies the caller (SEC-15).
        logger.warning("rate_limited", extra={"rule": error.rule.value, "path": request.url.path})
        raise


def _caller(request: Request) -> str:
    # require_api_key has already refused a request without the key, so the key is
    # there; its digest identifies the caller without keeping the key in memory.
    key = request.headers.get(API_KEY_HEADER, "")
    return hashlib.sha256(key.encode()).hexdigest()[:16]
