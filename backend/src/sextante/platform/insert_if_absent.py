"""Insert a row unless one with the same key exists, in portable SQL (02-arquitectura.md §5)."""

from collections.abc import Mapping

from sqlalchemy import Table, and_, exists, literal, select
from sqlalchemy.ext.asyncio import AsyncConnection


async def insert_if_absent(
    connection: AsyncConnection, table: Table, values: Mapping[str, object], key: tuple[str, ...]
) -> bool:
    """Insert ``values`` unless a row with the same ``key`` columns exists; True if inserted.

    ``INSERT ... SELECT ... WHERE NOT EXISTS`` is standard SQL, unlike SQLite's
    ``INSERT OR IGNORE``. On SQLite the insert takes the write lock, so a concurrent
    caller waits and then finds the row; the primary key stays the last guard.

    Example:
        inserted = await insert_if_absent(connection, TABLE, {"id": "a", ...}, ("id",))
    """
    columns = list(values)
    same_key = and_(*(table.c[name] == values[name] for name in key))
    rows = select(*(literal(values[name]) for name in columns)).where(~exists().where(same_key))
    result = await connection.execute(table.insert().from_select(columns, rows))
    return result.rowcount == 1
