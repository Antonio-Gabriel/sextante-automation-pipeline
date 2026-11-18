"""A monotonic clock and sleep the test holds, for waits measured in windows (SEC-12)."""

import asyncio
import threading
from typing import Final

# Retry backoffs are seconds; a ceiling wait is part of a window, here of an hour.
HELD_SLEEP_SECONDS: Final = 60.0
POLL_SECONDS: Final = 0.01


class HeldClock:
    """A monotonic clock that moves only when a long sleep is released.

    A sleep of a minute or more blocks until the test calls ``release``; then the clock
    moves by the seconds asked, as if they had passed, and ``sleeps`` records them. A
    retry's short backoff passes at once, without moving the clock.

    Example:
        clock = HeldClock()
        AppDependencies(monotonic=clock, sleep=clock.sleep)
        clock.release()
    """

    def __init__(self, released: bool = False) -> None:
        self.seconds = 1000.0
        self.sleeps: list[float] = []
        self._released = threading.Event()
        if released:
            self._released.set()

    def __call__(self) -> float:
        return self.seconds

    def release(self) -> None:
        """Let every held sleep, and every later one, through."""
        self._released.set()

    async def sleep(self, seconds: float) -> None:
        """Hold a long sleep until released, then move the clock by ``seconds``."""
        if seconds < HELD_SLEEP_SECONDS:
            return
        self.sleeps.append(seconds)
        while not self._released.is_set():
            await asyncio.sleep(POLL_SECONDS)
        self.seconds += seconds
