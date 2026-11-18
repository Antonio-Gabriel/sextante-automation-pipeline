"""Prompt cache tokens of each model call (REQ-AUD-004, CHG-0042).

``input_tokens`` keeps counting the input not served from the cache; the two new
columns count what was written to and read from the cache, which are priced apart.

Revision ID: 0008
Revises: 0007
"""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the cache write and cache read token counts, zero for earlier calls."""
    with op.batch_alter_table("model_call") as batch:
        batch.add_column(
            sa.Column("cache_creation_input_tokens", sa.Integer, nullable=False, server_default="0")
        )
        batch.add_column(
            sa.Column("cache_read_input_tokens", sa.Integer, nullable=False, server_default="0")
        )


def downgrade() -> None:
    """Drop the two columns."""
    with op.batch_alter_table("model_call") as batch:
        batch.drop_column("cache_read_input_tokens")
        batch.drop_column("cache_creation_input_tokens")
