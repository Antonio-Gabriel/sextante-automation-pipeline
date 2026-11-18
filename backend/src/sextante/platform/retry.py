"""Retries with exponential backoff for transient failures (REQ-PLT-003)."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

Sleep = Callable[[float], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """How many attempts in total, and the delay before the first retry.

    Example:
        RetryPolicy(max_attempts=3, base_delay_seconds=1.0)  # waits 1 s, then 2 s
    """

    max_attempts: int
    base_delay_seconds: float


async def call_with_retries[Result](
    operation: Callable[[], Awaitable[Result]],
    retryable: type[Exception],
    policy: RetryPolicy,
    sleep: Sleep,
) -> Result:
    """Run the operation, retrying only ``retryable`` failures with exponential backoff.

    Any other failure propagates at once: retrying a malformed answer is hoping luck
    changes (REQ-PLT-003, SEC-14).

    Example:
        await call_with_retries(lambda: classifier.choose(request), Unavailable, policy, sleep)
    """
    for attempt in range(1, policy.max_attempts):
        try:
            return await operation()
        except retryable:
            await sleep(policy.base_delay_seconds * 2 ** (attempt - 1))
    return await operation()
