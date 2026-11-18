"""Tables owned by the ingestion module (02-arquitectura.md §5)."""

from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text, UniqueConstraint

from sextante.platform.schema import SCHEMA_METADATA

JOB_TABLE = Table(
    "job",
    SCHEMA_METADATA,
    Column("id", String(64), primary_key=True),
    Column("status", String(16), nullable=False),
    Column("correlation_id", String(64), nullable=False),
    Column("worker_id", String(64), nullable=True),
    Column("created_at", String(40), nullable=False),
    Column("claimed_at", String(40), nullable=True),
    Column("finished_at", String(40), nullable=True),
)

INVOICE_TABLE = Table(
    "invoice",
    SCHEMA_METADATA,
    Column("id", String(64), primary_key=True),
    Column("job_id", String(64), ForeignKey("job.id"), nullable=False),
    Column("content_digest", String(64), nullable=False),
    Column("display_name", String(255), nullable=False),
    Column("storage_name", String(80), nullable=False),
    Column("file_format", String(8), nullable=False),
    Column("status", String(24), nullable=False),
    Column("status_reason", String(64), nullable=True),
    Column("created_at", String(40), nullable=False),
    # The idempotency key is a table constraint, not a check in code (REQ-ING-007).
    UniqueConstraint("content_digest", name="uq_invoice_content_digest"),
)

INVOICE_HEADER_TABLE = Table(
    "invoice_header",
    SCHEMA_METADATA,
    Column("invoice_id", String(64), ForeignKey("invoice.id"), primary_key=True),
    Column("supplier_name", Text, nullable=True),
    Column("supplier_nif", String(32), nullable=True),
    Column("invoice_number", String(64), nullable=True),
    Column("invoice_date", String(32), nullable=True),
    Column("currency", String(8), nullable=True),
    Column("billed_entities", Text, nullable=False),
    Column("summary_rows", Text, nullable=False),
    Column("notes", Text, nullable=False),
    Column("target_sheet", String(16), nullable=True),
    Column("entity_verdict", String(16), nullable=True),
    Column("entity_reason", String(40), nullable=True),
)

INVOICE_LINE_TABLE = Table(
    "invoice_line",
    SCHEMA_METADATA,
    Column("id", String(64), primary_key=True),
    Column("invoice_id", String(64), ForeignKey("invoice.id"), nullable=False),
    Column("position", Integer, nullable=False),
    Column("description", Text, nullable=False),
    Column("normalized_description", Text, nullable=False),
    Column("quantity", String(32), nullable=True),
    Column("unit_price", String(32), nullable=True),
    Column("vat_rate", String(16), nullable=True),
    Column("amount", String(32), nullable=True),
    UniqueConstraint("invoice_id", "position", name="uq_invoice_line_position"),
)
