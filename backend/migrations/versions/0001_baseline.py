"""Baseline revision: an empty schema under migration control.

The tables of jobs, invoices and encoded lines arrive with the tickets that use them.

Revision ID: 0001
Revises:
"""

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Nothing to create yet: the baseline only puts the database under Alembic."""


def downgrade() -> None:
    """Nothing to drop."""
