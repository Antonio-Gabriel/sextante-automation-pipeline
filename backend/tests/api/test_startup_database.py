"""The database is born from the migrations, with the SQLite conditions of D-3.5 on."""

import pytest
from sqlalchemy import text

from sextante.main import create_app


@pytest.mark.requirement("D-3.5", "REQ-PLT-008")
async def test_startup_applies_migrations_up_to_the_latest_revision(
    valid_environment: dict[str, str],
) -> None:
    """A fresh install gets its schema from Alembic, not from scattered CREATE TABLE."""
    app = create_app(valid_environment)

    async with app.router.lifespan_context(app), app.state.database_engine.connect() as connection:
        revision = (
            await connection.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one()

    assert revision == "0007"


@pytest.mark.requirement("D-3.5")
@pytest.mark.parametrize(
    ("pragma", "expected"),
    [("journal_mode", "wal"), ("foreign_keys", 1), ("busy_timeout", 5000)],
)
async def test_every_database_connection_has_the_mandatory_sqlite_pragmas(
    valid_environment: dict[str, str], pragma: str, expected: str | int
) -> None:
    """WAL, foreign keys and a busy timeout are on for every connection (02-arquitectura.md §5)."""
    app = create_app(valid_environment)

    async with app.router.lifespan_context(app), app.state.database_engine.connect() as connection:
        value = (await connection.execute(text(f"PRAGMA {pragma}"))).scalar_one()

    assert value == expected
