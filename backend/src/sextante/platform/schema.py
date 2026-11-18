"""Shared SQLAlchemy metadata. Each module declares its own tables on it.

The schema itself is created and evolved by the Alembic revisions in backend/migrations
(D-3.5), never by metadata.create_all().
"""

from sqlalchemy import MetaData

SCHEMA_METADATA = MetaData()
