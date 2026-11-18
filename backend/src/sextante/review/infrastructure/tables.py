"""Tables of the review module (migration 0006)."""

from sqlalchemy import Column, ForeignKey, String, Table, Text

from sextante.platform.schema import SCHEMA_METADATA

LINE_REVIEW_TABLE = Table(
    "line_review",
    SCHEMA_METADATA,
    Column("encoded_line_id", String(64), ForeignKey("encoded_line.id"), primary_key=True),
    Column("review_status", String(16), nullable=False),
    Column("item_number", String(32), nullable=True),
    Column("catalog_description", Text, nullable=True),
    Column("note", Text, nullable=True),
    Column("reviewed_by", String(128), nullable=False),
    Column("reviewed_at", String(40), nullable=False),
)
