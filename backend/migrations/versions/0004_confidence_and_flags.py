"""Confidence, review status and flags of each line (D-3.8, REQ-CNF-001 to REQ-CNF-004).

Lines of an ambiguous invoice are recorded uncoded, with no target sheet and no model
call, so those two columns become nullable (D-3.15, L-13).

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add confidence and review columns, relax two columns, create line_flag."""
    with op.batch_alter_table("encoded_line") as batch:
        batch.add_column(
            sa.Column("confidence", sa.String(8), nullable=False, server_default="LOW")
        )
        batch.add_column(
            sa.Column("confidence_rule", sa.String(32), nullable=False, server_default="unknown")
        )
        batch.add_column(
            sa.Column("review_status", sa.String(16), nullable=False, server_default="pending")
        )
        batch.alter_column("target_sheet", existing_type=sa.String(16), nullable=True)
        batch.alter_column("model_call_id", existing_type=sa.String(64), nullable=True)
    op.create_table(
        "line_flag",
        sa.Column(
            "encoded_line_id", sa.String(64), sa.ForeignKey("encoded_line.id"), primary_key=True
        ),
        sa.Column("reason", sa.String(40), primary_key=True),
    )


def downgrade() -> None:
    """Drop line_flag and the added columns. Uncoded lines must be deleted first."""
    op.drop_table("line_flag")
    with op.batch_alter_table("encoded_line") as batch:
        batch.alter_column("model_call_id", existing_type=sa.String(64), nullable=False)
        batch.alter_column("target_sheet", existing_type=sa.String(16), nullable=False)
        batch.drop_column("review_status")
        batch.drop_column("confidence_rule")
        batch.drop_column("confidence")
