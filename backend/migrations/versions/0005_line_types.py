"""Line type of each invoice line, and a note on its coding (REQ-ING-006, D-3.17).

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add invoice_line.line_type (existing lines are services) and encoded_line.note."""
    with op.batch_alter_table("invoice_line") as batch:
        batch.add_column(
            sa.Column("line_type", sa.String(16), nullable=False, server_default="service")
        )
    with op.batch_alter_table("encoded_line") as batch:
        batch.add_column(sa.Column("note", sa.String(32), nullable=True))


def downgrade() -> None:
    """Drop the two columns."""
    with op.batch_alter_table("encoded_line") as batch:
        batch.drop_column("note")
    with op.batch_alter_table("invoice_line") as batch:
        batch.drop_column("line_type")
