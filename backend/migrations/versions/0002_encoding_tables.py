"""Jobs, invoices, lines, coding results, model calls and the append-only audit trail.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

TIMESTAMP = sa.String(40)
IDENTIFIER = sa.String(64)


def upgrade() -> None:
    """Create the coding tables and make audit_event append-only (SEC-04)."""
    _create_ingestion_tables()
    _create_matching_tables()
    _create_audit_table()


def downgrade() -> None:
    """Drop everything this revision created, dependants first."""
    op.execute("DROP TRIGGER IF EXISTS audit_event_is_append_only_on_update")
    op.execute("DROP TRIGGER IF EXISTS audit_event_is_append_only_on_delete")
    for table in (
        "audit_event",
        "lexical_score",
        "encoded_line",
        "model_call",
        "invoice_line",
        "invoice_header",
        "invoice",
        "job",
    ):
        op.drop_table(table)


def _create_ingestion_tables() -> None:
    op.create_table(
        "job",
        sa.Column("id", IDENTIFIER, primary_key=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("correlation_id", IDENTIFIER, nullable=False),
        sa.Column("worker_id", IDENTIFIER, nullable=True),
        sa.Column("created_at", TIMESTAMP, nullable=False),
        sa.Column("claimed_at", TIMESTAMP, nullable=True),
        sa.Column("finished_at", TIMESTAMP, nullable=True),
    )
    op.create_table(
        "invoice",
        sa.Column("id", IDENTIFIER, primary_key=True),
        sa.Column("job_id", IDENTIFIER, sa.ForeignKey("job.id"), nullable=False),
        sa.Column("content_digest", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("storage_name", sa.String(80), nullable=False),
        sa.Column("file_format", sa.String(8), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("status_reason", sa.String(64), nullable=True),
        sa.Column("created_at", TIMESTAMP, nullable=False),
        sa.UniqueConstraint("content_digest", name="uq_invoice_content_digest"),
    )
    op.create_table(
        "invoice_header",
        sa.Column("invoice_id", IDENTIFIER, sa.ForeignKey("invoice.id"), primary_key=True),
        sa.Column("supplier_name", sa.Text, nullable=True),
        sa.Column("supplier_nif", sa.String(32), nullable=True),
        sa.Column("invoice_number", sa.String(64), nullable=True),
        sa.Column("invoice_date", sa.String(32), nullable=True),
        sa.Column("currency", sa.String(8), nullable=True),
        sa.Column("billed_entities", sa.Text, nullable=False),
        sa.Column("summary_rows", sa.Text, nullable=False),
        sa.Column("notes", sa.Text, nullable=False),
        sa.Column("target_sheet", sa.String(16), nullable=True),
    )
    op.create_table(
        "invoice_line",
        sa.Column("id", IDENTIFIER, primary_key=True),
        sa.Column("invoice_id", IDENTIFIER, sa.ForeignKey("invoice.id"), nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("normalized_description", sa.Text, nullable=False),
        sa.Column("quantity", sa.String(32), nullable=True),
        sa.Column("unit_price", sa.String(32), nullable=True),
        sa.Column("vat_rate", sa.String(16), nullable=True),
        sa.Column("amount", sa.String(32), nullable=True),
        sa.UniqueConstraint("invoice_id", "position", name="uq_invoice_line_position"),
    )


def _create_matching_tables() -> None:
    op.create_table(
        "model_call",
        sa.Column("id", IDENTIFIER, primary_key=True),
        sa.Column("invoice_id", IDENTIFIER, sa.ForeignKey("invoice.id"), nullable=False),
        sa.Column("model_id", sa.String(128), nullable=False),
        sa.Column("prompt_version", sa.String(64), nullable=False),
        sa.Column("input_tokens", sa.Integer, nullable=False),
        sa.Column("output_tokens", sa.Integer, nullable=False),
        sa.Column("called_at", TIMESTAMP, nullable=False),
    )
    op.create_table(
        "encoded_line",
        sa.Column("id", IDENTIFIER, primary_key=True),
        sa.Column("invoice_line_id", IDENTIFIER, sa.ForeignKey("invoice_line.id"), nullable=False),
        sa.Column("target_sheet", sa.String(16), nullable=False),
        sa.Column("item_number", sa.String(32), nullable=True),
        sa.Column("catalog_description", sa.Text, nullable=True),
        sa.Column("choice_outcome", sa.String(24), nullable=False),
        sa.Column("candidate_index", sa.Integer, nullable=True),
        sa.Column("catalog_digest", sa.String(64), nullable=False),
        sa.Column("model_call_id", IDENTIFIER, sa.ForeignKey("model_call.id"), nullable=False),
        sa.Column("encoded_at", TIMESTAMP, nullable=False),
        sa.UniqueConstraint("invoice_line_id", name="uq_encoded_line_invoice_line"),
    )
    op.create_table(
        "lexical_score",
        sa.Column(
            "invoice_line_id", IDENTIFIER, sa.ForeignKey("invoice_line.id"), primary_key=True
        ),
        sa.Column("item_number", sa.String(32), primary_key=True),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("rank", sa.Integer, nullable=False),
    )


def _create_audit_table() -> None:
    op.create_table(
        "audit_event",
        sa.Column("id", IDENTIFIER, primary_key=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("subject_type", sa.String(64), nullable=False),
        sa.Column("subject_id", IDENTIFIER, nullable=False),
        sa.Column("payload", sa.Text, nullable=False),
        sa.Column("author", sa.String(128), nullable=False),
        sa.Column("recorded_at", TIMESTAMP, nullable=False),
    )
    # SQLite has no per-table privileges, so append-only is enforced by triggers at the
    # data layer, not only by the repository having no update method (SEC-04).
    for operation in ("UPDATE", "DELETE"):
        op.execute(
            f"CREATE TRIGGER audit_event_is_append_only_on_{operation.lower()} "
            f"BEFORE {operation} ON audit_event "
            "BEGIN SELECT RAISE(ABORT, 'audit_event is append-only'); END"
        )
