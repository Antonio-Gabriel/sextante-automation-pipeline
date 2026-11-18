"""The model call ceiling on its own: windows, counting and the observer (SEC-12)."""

import pytest

from sextante.platform.model_call_ceiling import ModelCallCeiling
from sextante.platform.rate_limit import HOUR, RateLimit
from tests.fakes.held_clock import HeldClock


class _Observer:
    def __init__(self) -> None:
        self.events: list[str] = []

    async def waiting(self, seconds: float) -> None:
        self.events.append(f"waiting {seconds}")

    async def released(self) -> None:
        self.events.append("released")


def _ceiling(requests: int, clock: HeldClock, observer: _Observer) -> ModelCallCeiling:
    return ModelCallCeiling(RateLimit(requests, HOUR), clock, clock.sleep, observer)


@pytest.mark.requirement("SEC-12")
async def test_calls_within_the_ceiling_never_wait() -> None:
    """Two calls under a ceiling of two: no sleep, nothing told."""
    clock, observer = HeldClock(released=True), _Observer()
    ceiling = _ceiling(2, clock, observer)

    await ceiling.acquire()
    await ceiling.acquire()

    assert (clock.sleeps, observer.events) == ([], [])


@pytest.mark.requirement("SEC-12")
async def test_a_call_over_the_ceiling_waits_for_the_next_window_and_counts_there() -> None:
    """At 1000 s the hour ends at 3600 s: the third call waits 2600 s, then uses the new hour."""
    clock, observer = HeldClock(released=True), _Observer()
    ceiling = _ceiling(2, clock, observer)
    for _ in range(3):
        await ceiling.acquire()

    assert clock.sleeps == [2600.0]
    assert observer.events == ["waiting 2600.0", "released"]
    # One call used in the new window: one more fits, the next does not.
    assert ceiling.wait_seconds() == 0.0
    await ceiling.acquire()
    assert ceiling.wait_seconds() == 3600.0


@pytest.mark.requirement("SEC-12")
async def test_a_new_window_starts_the_count_again() -> None:
    """A full window that has passed leaves no trace in the next one."""
    clock, observer = HeldClock(released=True), _Observer()
    ceiling = _ceiling(1, clock, observer)
    await ceiling.acquire()
    clock.seconds = 3600.0

    assert ceiling.wait_seconds() == 0.0
