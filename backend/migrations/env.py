"""Alembic environment. The connection is always supplied by apply_migrations()."""

from alembic import context
from sqlalchemy import Connection

connection: Connection = context.config.attributes["connection"]
context.configure(connection=connection, render_as_batch=True)

with context.begin_transaction():
    context.run_migrations()
