"""Deterministic Clock and IdentifierGenerator for tests (NFR-TST-003)."""

from datetime import UTC, datetime, timedelta


class FixedClock:
    """A clock that starts at a fixed instant and advances one second per reading.

    Example:
        clock = FixedClock()
    """

    def __init__(self, start: datetime = datetime(2026, 11, 18, 9, 0, tzinfo=UTC)) -> None:
        self._now = start

    def now(self) -> datetime:
        """Return the current instant, then advance by one second."""
        current = self._now
        self._now += timedelta(seconds=1)
        return current


class SequentialIdentifierGenerator:
    """Identifiers id-0001, id-0002, ... in call order.

    Example:
        ids = SequentialIdentifierGenerator()
    """

    def __init__(self) -> None:
        self._count = 0

    def new_id(self) -> str:
        """Return the next identifier."""
        self._count += 1
        return f"id-{self._count:04d}"
