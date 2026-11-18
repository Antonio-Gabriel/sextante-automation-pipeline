"""Database engine and migrations (D-3.5, 02-arquitectura.md §5)."""

from pathlib import Path
from typing import Final

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import ConnectionPoolEntry

# backend/migrations, as laid out in 02-arquitectura.md §2.4. This file sits at
# backend/src/sextante/platform/, three levels below backend/.
MIGRATIONS_DIRECTORY: Final = Path(__file__).resolve().parents[3] / "migrations"
ASYNC_DRIVER: Final = "+aiosqlite"

# The three SQLite conditions that are not optional (D-3.5). foreign_keys is the most
# treacherous: SQLite disables it by default and silently accepts orphan rows.
SQLITE_PRAGMAS: Final = (
    "PRAGMA journal_mode = WAL",
    "PRAGMA foreign_keys = ON",
    "PRAGMA busy_timeout = 5000",
)


def create_database_engine(database_url: str) -> AsyncEngine:
    """Create the async engine with the mandatory pragmas applied to every connection.

    Example:
        engine = create_database_engine("sqlite+aiosqlite:///./sextante.db")
    """
    engine = create_async_engine(database_url)
    event.listen(engine.sync_engine, "connect", _set_sqlite_pragmas)
    return engine


def apply_migrations(database_url: str) -> None:
    """Bring the schema to the latest Alembic revision. Runs synchronously at startup.

    Example:
        apply_migrations("sqlite+aiosqlite:///./sextante.db")
    """
    sync_engine = create_engine(database_url.replace(ASYNC_DRIVER, ""))
    event.listen(sync_engine, "connect", _set_sqlite_pragmas)
    try:
        with sync_engine.begin() as connection:
            config = Config()
            config.set_main_option("script_location", str(MIGRATIONS_DIRECTORY))
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
    finally:
        sync_engine.dispose()


def _set_sqlite_pragmas(dbapi_connection: DBAPIConnection, _record: ConnectionPoolEntry) -> None:
    cursor = dbapi_connection.cursor()
    try:
        for pragma in SQLITE_PRAGMAS:
            cursor.execute(pragma)
    finally:
        cursor.close()
