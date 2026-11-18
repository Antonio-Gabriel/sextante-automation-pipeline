"""HTTP idempotency for POST and PATCH (SEC-19).

The key is scoped by identity, method and path, and carries a fingerprint of the body.
The record is written in the same transaction as the operation, so two concurrent
requests with the same key cannot both act; the same key with another body is refused.
"""

import hashlib
import json
import re
from collections.abc import Awaitable, Callable, Mapping
from datetime import timedelta
from typing import Final

from sqlalchemy import Column, Integer, String, Table, Text, delete, select, update
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from sextante.platform.clock import Clock
from sextante.platform.errors import DomainError
from sextante.platform.schema import SCHEMA_METADATA

IDEMPOTENCY_RETENTION: Final = timedelta(hours=24)
IDEMPOTENCY_KEY_PATTERN: Final = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
PENDING_STATUS: Final = 0

IDEMPOTENCY_TABLE = Table(
    "idempotency_record",
    SCHEMA_METADATA,
    Column("scope", String(400), primary_key=True),
    Column("idempotency_key", String(128), primary_key=True),
    Column("fingerprint", String(64), nullable=False),
    Column("status_code", Integer, nullable=False),
    Column("response_body", Text, nullable=False),
    Column("created_at", String(40), nullable=False),
)

JsonBody = Mapping[str, object]
Operation = Callable[[AsyncConnection], Awaitable[tuple[int, JsonBody]]]


class IdempotencyKeyRequiredError(DomainError):
    """A POST or PATCH arrived without a valid Idempotency-Key header."""

    user_message_key = "errors.idempotency.key_required"


class IdempotencyKeyReusedError(DomainError):
    """The key was already used for a request with another body."""

    user_message_key = "errors.idempotency.key_reused"


def require_key(header_value: str | None) -> str:
    """Return the Idempotency-Key, or refuse a missing or malformed one.

    Example:
        key = require_key(request.headers.get("Idempotency-Key"))
    """
    if header_value is None or not IDEMPOTENCY_KEY_PATTERN.fullmatch(header_value):
        raise IdempotencyKeyRequiredError(
            "Idempotency-Key is missing or malformed. Expected 1 to 128 characters of "
            "letters, digits, '.', '_', ':' or '-'."
        )
    return header_value


def body_fingerprint(body: JsonBody) -> str:
    """SHA-256 of the body in canonical JSON, so equal bodies give equal prints.

    Example:
        body_fingerprint({"item_number": "O00051"})
    """
    canonical = json.dumps(body, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class IdempotentExecutor:
    """Run an operation once per (scope, key), and replay its answer afterwards.

    Example:
        status, body = await executor.run(scope, key, fingerprint, operation)
    """

    def __init__(self, engine: AsyncEngine, clock: Clock) -> None:
        self._engine = engine
        self._clock = clock

    async def run(
        self, scope: str, key: str, fingerprint: str, operation: Operation
    ) -> tuple[int, JsonBody]:
        """Return the stored answer for a repeated request, or run the operation now.

        Raises:
            IdempotencyKeyReusedError: when the key was used with another body.
        """
        async with self._engine.begin() as connection:
            await self._purge_expired(connection)
            stored = await _stored(connection, scope, key)
            if stored is not None:
                return _replay(stored, fingerprint)
            # The reservation comes first: a concurrent request with the same key fails on
            # the primary key instead of acting a second time.
            await connection.execute(
                IDEMPOTENCY_TABLE.insert().values(
                    scope=scope,
                    idempotency_key=key,
                    fingerprint=fingerprint,
                    status_code=PENDING_STATUS,
                    response_body="",
                    created_at=self._clock.now().isoformat(),
                )
            )
            status, body = await operation(connection)
            await _store_answer(connection, scope, key, (status, body))
        return status, body

    async def _purge_expired(self, connection: AsyncConnection) -> None:
        # Stored answers are kept 24 hours: keeping them longer would keep invoice data
        # without need (SEC-19).
        cutoff = (self._clock.now() - IDEMPOTENCY_RETENTION).isoformat()
        await connection.execute(
            delete(IDEMPOTENCY_TABLE).where(IDEMPOTENCY_TABLE.c.created_at < cutoff)
        )


async def _store_answer(
    connection: AsyncConnection, scope: str, key: str, answer: tuple[int, JsonBody]
) -> None:
    status, body = answer
    table = IDEMPOTENCY_TABLE
    await connection.execute(
        update(table)
        .where(table.c.scope == scope, table.c.idempotency_key == key)
        .values(status_code=status, response_body=json.dumps(body, ensure_ascii=False, default=str))
    )


async def _stored(connection: AsyncConnection, scope: str, key: str) -> tuple[str, int, str] | None:
    query = select(
        IDEMPOTENCY_TABLE.c.fingerprint,
        IDEMPOTENCY_TABLE.c.status_code,
        IDEMPOTENCY_TABLE.c.response_body,
    ).where(IDEMPOTENCY_TABLE.c.scope == scope, IDEMPOTENCY_TABLE.c.idempotency_key == key)
    row = (await connection.execute(query)).first()
    return (str(row[0]), int(row[1]), str(row[2])) if row else None


def _replay(stored: tuple[str, int, str], fingerprint: str) -> tuple[int, JsonBody]:
    stored_fingerprint, status, body = stored
    if stored_fingerprint != fingerprint:
        raise IdempotencyKeyReusedError(
            "Idempotency-Key was already used with another request body. Expected a new key."
        )
    loaded: JsonBody = json.loads(body)
    return status, loaded
