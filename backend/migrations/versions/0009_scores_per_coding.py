"""Lexical scores belong to a coding, not to a line (ticket 14, NFR-REL-002).

A line coded again keeps its earlier coding as superseded (migration 0007); its scores
must stay with that coding too, so the key becomes (encoded_line_id, item_number).
Existing scores move to the coding in force of their line.

Revision ID: 0009
Revises: 0008
"""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Rebuild lexical_score keyed by the coding."""
    op.create_table(
        "lexical_score_by_coding",
        sa.Column(
            "encoded_line_id", sa.String(64), sa.ForeignKey("encoded_line.id"), primary_key=True
        ),
        sa.Column("item_number", sa.String(32), primary_key=True),
        sa.Column(
            "invoice_line_id", sa.String(64), sa.ForeignKey("invoice_line.id"), nullable=False
        ),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("rank", sa.Integer, nullable=False),
    )
    op.execute(
        "INSERT INTO lexical_score_by_coding "
        "(encoded_line_id, item_number, invoice_line_id, score, rank) "
        "SELECT e.id, s.item_number, s.invoice_line_id, s.score, s.rank "
        "FROM lexical_score s JOIN encoded_line e "
        "ON e.invoice_line_id = s.invoice_line_id AND e.superseded_at IS NULL"
    )
    op.drop_table("lexical_score")
    op.rename_table("lexical_score_by_coding", "lexical_score")


def downgrade() -> None:
    """Key the scores by line again, keeping those of the codings in force only."""
    op.create_table(
        "lexical_score_by_line",
        sa.Column(
            "invoice_line_id", sa.String(64), sa.ForeignKey("invoice_line.id"), primary_key=True
        ),
        sa.Column("item_number", sa.String(32), primary_key=True),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("rank", sa.Integer, nullable=False),
    )
    op.execute(
        "INSERT INTO lexical_score_by_line (invoice_line_id, item_number, score, rank) "
        "SELECT s.invoice_line_id, s.item_number, s.score, s.rank "
        "FROM lexical_score s JOIN encoded_line e "
        "ON e.id = s.encoded_line_id AND e.superseded_at IS NULL"
    )
    op.drop_table("lexical_score")
    op.rename_table("lexical_score_by_line", "lexical_score")
