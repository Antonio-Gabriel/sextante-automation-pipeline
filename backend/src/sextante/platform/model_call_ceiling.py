"""A ceiling on model calls per window, the limit that protects the budget (SEC-12).

Every model call takes room under the ceiling first, retries included, because every
attempt is paid. Over the ceiling the call waits for the next window: the invoice it
belongs to stays queued and is coded later, delayed, never refused nor lost. An
observer is told when a wait starts and ends, so the job can show it.

Like the rate limits, the count lives in this process's memory: it starts again at
zero on a restart, and two workers would each allow the full ceiling (SEC-12,
00-decisoes-e-lacunas.md §6).
"""

from typing import Protocol

from sextante.platform.rate_limit import Monotonic, RateLimit
from sextante.platform.retry import Sleep


class CeilingObserver(Protocol):
    """Told when a model call starts and stops waiting for the ceiling."""

    async def waiting(self, seconds: float) -> None:
        """A call waits ``seconds`` for the next window."""
        ...

    async def released(self) -> None:
        """The call that waited has room now."""
        ...


class ModelCallCeiling:
    """Count model calls in fixed windows of a monotonic clock; wait when the window is full.

    Example:
        ceiling = ModelCallCeiling(RateLimit(200, HOUR), time.monotonic, asyncio.sleep, observer)
        await ceiling.acquire()  # before each model call
    """

    def __init__(
        self, limit: RateLimit, monotonic: Monotonic, sleep: Sleep, observer: CeilingObserver
    ) -> None:
        self._limit = limit
        self._monotonic = monotonic
        self._sleep = sleep
        self._observer = observer
        self._window = -1
        self._used = 0

    def wait_seconds(self) -> float:
        """Seconds until a call fits, 0 when one fits now.

        Example:
            ceiling.wait_seconds()  # 2600.0 when the hour is used up at 1000 s
        """
        now = self._monotonic()
        if self._limit.window_at(now) != self._window or self._used < self._limit.requests:
            return 0.0
        return self._limit.seconds_left(now)

    async def acquire(self) -> None:
        """Wait until a call fits, telling the observer, then count the call.

        Example:
            await ceiling.acquire()
        """
        wait = self.wait_seconds()
        if wait > 0:
            await self._observer.waiting(wait)
            while (wait := self.wait_seconds()) > 0:
                await self._sleep(wait)
            await self._observer.released()
        window = self._limit.window_at(self._monotonic())
        self._used = self._used + 1 if window == self._window else 1
        self._window = window
