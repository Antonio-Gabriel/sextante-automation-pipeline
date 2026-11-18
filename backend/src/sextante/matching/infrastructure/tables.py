"""Tables owned by the matching module (02-arquitectura.md §5)."""

from sqlalchemy import Column, Float, ForeignKey, Index, Integer, String, Table, Text, text

from sextante.platform.schema import SCHEMA_METADATA

MODEL_CALL_TABLE = Table(
    "model_call",
    SCHEMA_METADATA,
    Column("id", String(64), primary_key=True),
    Column("invoice_id", String(64), ForeignKey("invoice.id"), nullable=False),
    Column("model_id", String(128), nullable=False),
    Column("prompt_version", String(64), nullable=False),
    Column("input_tokens", Integer, nullable=False),
    Column("output_tokens", Integer, nullable=False),
    Column("called_at", String(40), nullable=False),
)

ENCODED_LINE_TABLE = Table(
    "encoded_line",
    SCHEMA_METADATA,
    Column("id", String(64), primary_key=True),
    Column("invoice_line_id", String(64), ForeignKey("invoice_line.id"), nullable=False),
    Column("target_sheet", String(16), nullable=True),
    Column("item_number", String(32), nullable=True),
    Column("catalog_description", Text, nullable=True),
    Column("choice_outcome", String(24), nullable=False),
    Column("candidate_index", Integer, nullable=True),
    Column("catalog_digest", String(64), nullable=False),
    Column("model_call_id", String(64), ForeignKey("model_call.id"), nullable=True),
    Column("confidence", String(8), nullable=False),
    Column("confidence_rule", String(32), nullable=False),
    Column("review_status", String(16), nullable=False),
    Column("note", String(32), nullable=True),
    Column("encoded_at", String(40), nullable=False),
    # Set when a later coding of the same line takes over (migration 0007).
    Column("superseded_at", String(40), nullable=True),
    Index(
        "uq_encoded_line_in_force",
        "invoice_line_id",
        unique=True,
        sqlite_where=text("superseded_at IS NULL"),
        postgresql_where=text("superseded_at IS NULL"),
    ),
)

LEXICAL_SCORE_TABLE = Table(
    "lexical_score",
    SCHEMA_METADATA,
    Column("invoice_line_id", String(64), ForeignKey("invoice_line.id"), primary_key=True),
    Column("item_number", String(32), primary_key=True),
    Column("score", Float, nullable=False),
    Column("rank", Integer, nullable=False),
)

LINE_FLAG_TABLE = Table(
    "line_flag",
    SCHEMA_METADATA,
    Column("encoded_line_id", String(64), ForeignKey("encoded_line.id"), primary_key=True),
    Column("reason", String(40), primary_key=True),
)
