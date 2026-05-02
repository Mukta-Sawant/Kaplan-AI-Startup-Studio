"""Add phase2_complete to submission_status_enum

Revision ID: 002
Revises: 001
Create Date: 2026-05-01 00:00:00.000000
"""

from typing import Sequence, Union
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL ALTER TYPE ADD VALUE cannot run inside a transaction block,
    # so we use a DO block that ignores "already exists" errors.
    op.execute("""
        DO $$ BEGIN
            ALTER TYPE submission_status_enum ADD VALUE IF NOT EXISTS 'phase2_complete';
        EXCEPTION WHEN others THEN NULL;
        END $$
    """)


def downgrade() -> None:
    # PostgreSQL does not support removing enum values; downgrade is a no-op.
    pass
