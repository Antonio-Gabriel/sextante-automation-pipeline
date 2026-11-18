"""Review state of each coded line, and idempotency records (REQ-REV-002 to 005, SEC-19).

The review state lives apart from encoded_line, so a correction never overwrites the
original coding record (REQ-REV-004); its history is in audit_event.

Revision ID: 0006
Revises: 0005
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create line_review and idempotency_record."""
    op.create_table(
        "line_review",
        sa.Column(
            "encoded_line_id", sa.String(64), sa.ForeignKey("encoded_line.id"), primary_key=True
        ),
        sa.Column("review_status", sa.String(16), nullable=False),
        sa.Column("item_number", sa.String(32), nullable=True),
        sa.Column("catalog_description", sa.Text, nullable=True),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("reviewed_by", sa.String(128), nullable=False),
        sa.Column("reviewed_at", sa.String(40), nullable=False),
    )
    op.create_table(
        "idempotency_record",
        sa.Column("scope", sa.String(400), primary_key=True),
        sa.Column("idempotency_key", sa.String(128), primary_key=True),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("status_code", sa.Integer, nullable=False),
        sa.Column("response_body", sa.Text, nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
    )


def downgrade() -> None:
    """Drop both tables."""
    op.drop_table("idempotency_record")
    op.drop_table("line_review")
