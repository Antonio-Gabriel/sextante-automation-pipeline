"""Append-only audit trail (D-3.11, REQ-AUD-001, REQ-AUD-002, SEC-04)."""

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Final

from sqlalchemy import Column, String, Table, Text
from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.platform.schema import SCHEMA_METADATA

AUDIT_EVENT_TABLE = Table(
    "audit_event",
    SCHEMA_METADATA,
    Column("id", String(64), primary_key=True),
    Column("event_type", String(64), nullable=False),
    Column("subject_type", String(64), nullable=False),
    Column("subject_id", String(64), nullable=False),
    Column("payload", Text, nullable=False),
    Column("author", String(128), nullable=False),
    Column("recorded_at", String(40), nullable=False),
)

SYSTEM_AUTHOR: Final = "system"


class AuditEventRepository:
    """The single writer of audit_event. It can only append (SEC-04).

    Example:
        await AuditEventRepository().append(connection, event_id, "line_encoded", ...)
    """

    async def append(
        self,
        connection: AsyncConnection,
        event_id: str,
        event_type: str,
        subject: tuple[str, str],
        payload: Mapping[str, object],
        recorded_at: datetime,
        author: str = SYSTEM_AUTHOR,
    ) -> None:
        """Insert one audit event inside the caller's transaction.

        Example:
            await audit.append(connection, event_id, "line_encoded", ("invoice_line", line_id),
                               {"item_number": "O00004"}, clock.now())
        """
        subject_type, subject_id = subject
        await connection.execute(
            AUDIT_EVENT_TABLE.insert().values(
                id=event_id,
                event_type=event_type,
                subject_type=subject_type,
                subject_id=subject_id,
                payload=json.dumps(payload, ensure_ascii=False, default=str, sort_keys=True),
                author=author,
                recorded_at=recorded_at.isoformat(),
            )
        )
