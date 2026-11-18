"""Entity verdict and its reason on the invoice header (D-3.15, REQ-ENT-004).

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the entity check result columns. Existing rows keep NULL: never checked."""
    with op.batch_alter_table("invoice_header") as batch:
        batch.add_column(sa.Column("entity_verdict", sa.String(16), nullable=True))
        batch.add_column(sa.Column("entity_reason", sa.String(40), nullable=True))


def downgrade() -> None:
    """Drop the entity check result columns."""
    with op.batch_alter_table("invoice_header") as batch:
        batch.drop_column("entity_reason")
        batch.drop_column("entity_verdict")
