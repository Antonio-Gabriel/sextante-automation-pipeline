"""Clock and identifier ports, injected so tests stay repeatable (NFR-TST-003)."""

import uuid
from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    """Port: the current instant, always timezone-aware UTC (D-3.5)."""

    def now(self) -> datetime:
        """Return the current instant in UTC."""
        ...


class IdentifierGenerator(Protocol):
    """Port: opaque unique identifiers. Never counters (D-3.10)."""

    def new_id(self) -> str:
        """Return a new unique identifier."""
        ...


class SystemClock:
    """Clock backed by the system time.

    Example:
        SystemClock().now()  # datetime(..., tzinfo=UTC)
    """

    def now(self) -> datetime:
        """Return the current instant in UTC."""
        return datetime.now(UTC)


class UuidIdentifierGenerator:
    """Random UUID4 identifiers, as hexadecimal text.

    Example:
        UuidIdentifierGenerator().new_id()  # "3f2a9c..."
    """

    def new_id(self) -> str:
        """Return a new random identifier."""
        return uuid.uuid4().hex
