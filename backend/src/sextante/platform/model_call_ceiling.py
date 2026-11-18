"""A ceiling on model calls per window, the limit that protects the budget (SEC-12).

The worker waits for room before the next invoice, so work over the ceiling stays
queued and is coded later: delayed, never refused nor lost. Every call counts,
retries included, because every attempt is paid.

Like the rate limits, the count lives in this process's memory: with two workers each
allows the full ceiling (SEC-12, 00-decisoes-e-lacunas.md §6).
"""

from sextante.platform.rate_limit import Monotonic, RateLimit
from sextante.platform.retry import Sleep


class ModelCallCeiling:
    """Count model calls in fixed windows of a monotonic clock; wait when the window is full.

    Example:
        ceiling = ModelCallCeiling(RateLimit(200, HOUR), time.monotonic, asyncio.sleep)
        await ceiling.acquire()  # before each model call
    """

    def __init__(self, limit: RateLimit, monotonic: Monotonic, sleep: Sleep) -> None:
        self._limit = limit
        self._monotonic = monotonic
        self._sleep = sleep
        self._window = -1
        self._used = 0

    def wait_seconds(self) -> float:
        """Seconds until a call fits, 0 when one fits now.

        Example:
            ceiling.wait_seconds()  # 2600.0 when the hour is used up at 1000 s
        """
        now = self._monotonic()
        window = int(now // self._limit.window_seconds)
        if window != self._window or self._used < self._limit.requests:
            return 0.0
        return (window + 1) * self._limit.window_seconds - now

    async def wait_for_room(self) -> None:
        """Sleep until a call fits, without counting one.

        Example:
            await ceiling.wait_for_room()
        """
        while (wait := self.wait_seconds()) > 0:
            await self._sleep(wait)

    async def acquire(self) -> None:
        """Wait until a call fits, then count it.

        Example:
            await ceiling.acquire()
        """
        await self.wait_for_room()
        window = int(self._monotonic() // self._limit.window_seconds)
        self._used = self._used + 1 if window == self._window else 1
        self._window = window
