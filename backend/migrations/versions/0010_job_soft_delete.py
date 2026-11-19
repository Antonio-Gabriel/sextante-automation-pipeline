"""A job can be deleted, softly: hidden from every read, its rows kept.

Uploading again a file of a deleted job restores that job (REQ-ING-007 keeps one
invoice per content), so nothing is lost and nothing is coded twice.

Revision ID: 0010
Revises: 0009
"""

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add job.deleted_at, empty for every existing job."""
    with op.batch_alter_table("job") as batch:
        batch.add_column(sa.Column("deleted_at", sa.String(40), nullable=True))


def downgrade() -> None:
    """Drop job.deleted_at; deleted jobs become visible again."""
    with op.batch_alter_table("job") as batch:
        batch.drop_column("deleted_at")
