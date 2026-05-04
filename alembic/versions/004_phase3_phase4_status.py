"""Add phase3_complete and phase4_complete to submission_status_enum

Revision ID: 004
Revises: 003
Create Date: 2026-05-03

"""
from typing import Sequence, Union

from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE submission_status_enum ADD VALUE IF NOT EXISTS 'phase3_complete'")
    op.execute("ALTER TYPE submission_status_enum ADD VALUE IF NOT EXISTS 'phase4_complete'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values without recreating the type.
    pass
