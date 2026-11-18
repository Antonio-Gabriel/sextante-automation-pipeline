"""Entity resolution, superseded codings and possible duplicates (REQ-REV-006, REQ-ING-011).

A resolved invoice is coded again: its earlier records are marked superseded, never
overwritten (REQ-REV-004), so a line has one coding in force and keeps the others.

Revision ID: 0007
Revises: 0006
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add entity_resolution, encoded_line.superseded_at and the duplicate columns."""
    op.create_table(
        "entity_resolution",
        sa.Column("invoice_id", sa.String(64), sa.ForeignKey("invoice.id"), primary_key=True),
        sa.Column("verdict", sa.String(16), nullable=False),
        sa.Column("note", sa.Text, nullable=False),
        sa.Column("resolved_by", sa.String(128), nullable=False),
        sa.Column("resolved_at", sa.String(40), nullable=False),
    )
    with op.batch_alter_table("encoded_line") as batch:
        batch.add_column(sa.Column("superseded_at", sa.String(40), nullable=True))
        batch.drop_constraint("uq_encoded_line_invoice_line", type_="unique")
    # One coding in force per line; superseded ones are kept beside it.
    op.create_index(
        "uq_encoded_line_in_force",
        "encoded_line",
        ["invoice_line_id"],
        unique=True,
        sqlite_where=sa.text("superseded_at IS NULL"),
        postgresql_where=sa.text("superseded_at IS NULL"),
    )
    with op.batch_alter_table("invoice_header") as batch:
        # NIF when extracted, normalized name otherwise. Rows stored before this revision
        # keep it empty and are never matched as duplicates.
        batch.add_column(sa.Column("supplier_key", sa.Text, nullable=True))
        batch.add_column(sa.Column("possible_duplicate_of", sa.String(64), nullable=True))
    op.create_index(
        "ix_invoice_header_supplier_number", "invoice_header", ["supplier_key", "invoice_number"]
    )


def downgrade() -> None:
    """Drop what this revision added.

    The unique constraint of 0006 allows one coding per line, so the superseded codings,
    and their flags, are deleted first. Their history stays in audit_event.
    """
    op.drop_index("ix_invoice_header_supplier_number", "invoice_header")
    with op.batch_alter_table("invoice_header") as batch:
        batch.drop_column("possible_duplicate_of")
        batch.drop_column("supplier_key")
    for dependant in (
        "DELETE FROM line_flag WHERE encoded_line_id IN "
        "(SELECT id FROM encoded_line WHERE superseded_at IS NOT NULL)",
        "DELETE FROM line_review WHERE encoded_line_id IN "
        "(SELECT id FROM encoded_line WHERE superseded_at IS NOT NULL)",
    ):
        op.execute(dependant)
    op.execute("DELETE FROM encoded_line WHERE superseded_at IS NOT NULL")
    op.drop_index("uq_encoded_line_in_force", "encoded_line")
    with op.batch_alter_table("encoded_line") as batch:
        batch.create_unique_constraint("uq_encoded_line_invoice_line", ["invoice_line_id"])
        batch.drop_column("superseded_at")
    op.drop_table("entity_resolution")
