"""SEC-19: one effect per Idempotency-Key, under concurrency, failure and expiry."""

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from sextante.platform.database import apply_migrations, create_database_engine
from sextante.platform.errors import DomainError
from sextante.platform.idempotency import (
    IdempotencyKeyReusedError,
    IdempotentExecutor,
    JsonBody,
)

SCOPE = "synthetic-reviewer:POST:/api/encoded-lines/x/accept"


class _SettableClock:
    def __init__(self) -> None:
        self.instant = datetime(2026, 11, 18, 9, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self.instant


class _CountingOperation:
    """An operation that takes a while, so two requests overlap, and counts its runs."""

    def __init__(self) -> None:
        self.runs = 0

    async def __call__(self, connection: AsyncConnection) -> tuple[int, JsonBody]:
        self.runs += 1
        await asyncio.sleep(0.05)
        return 200, {"run": self.runs}


@pytest.fixture
async def engine(tmp_path: Path) -> AsyncIterator[AsyncEngine]:
    url = f"sqlite+aiosqlite:///{tmp_path / 'idempotency.db'}"
    apply_migrations(url)
    engine = create_database_engine(url)
    yield engine
    await engine.dispose()


@pytest.mark.requirement("SEC-19")
async def test_two_simultaneous_requests_with_the_same_key_act_once(engine: AsyncEngine) -> None:
    """The second request waits for the first and gets its answer, never a 500."""
    executor = IdempotentExecutor(engine, _SettableClock())
    operation = _CountingOperation()

    answers = await asyncio.gather(
        executor.run(SCOPE, "k", "print", operation),
        executor.run(SCOPE, "k", "print", operation),
    )

    assert operation.runs == 1
    assert list(answers) == [(200, {"run": 1}), (200, {"run": 1})]


@pytest.mark.requirement("SEC-19")
async def test_a_refused_request_leaves_the_key_free(engine: AsyncEngine) -> None:
    """Nothing happened, so nothing is stored: the same key may be sent again."""
    executor = IdempotentExecutor(engine, _SettableClock())

    async def refused(connection: AsyncConnection) -> tuple[int, JsonBody]:
        raise DomainError("Refused for the test.")

    with pytest.raises(DomainError):
        await executor.run(SCOPE, "k", "print", refused)
    operation = _CountingOperation()
    answer = await executor.run(SCOPE, "k", "print", operation)

    assert (operation.runs, answer) == (1, (200, {"run": 1}))


@pytest.mark.requirement("SEC-19")
async def test_stored_answers_are_purged_after_24_hours(engine: AsyncEngine) -> None:
    """Before the purge the key is bound to its body; after it, the key is free again."""
    clock = _SettableClock()
    executor = IdempotentExecutor(engine, clock)
    await executor.run(SCOPE, "k", "first-body", _CountingOperation())

    with pytest.raises(IdempotencyKeyReusedError):
        await executor.run(SCOPE, "k", "second-body", _CountingOperation())
    clock.instant += timedelta(hours=24, seconds=1)
    purged = await executor.purge_expired()
    operation = _CountingOperation()
    await executor.run(SCOPE, "k", "second-body", operation)

    assert (purged, operation.runs) == (1, 1)
