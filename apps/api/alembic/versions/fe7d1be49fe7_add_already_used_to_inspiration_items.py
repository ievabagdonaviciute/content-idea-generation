"""add already_used to inspiration_items

Revision ID: fe7d1be49fe7
Revises: ef40bc825ed2
Create Date: 2026-07-27 20:58:56.731830

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fe7d1be49fe7"
down_revision: str | Sequence[str] | None = "ef40bc825ed2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # server_default backfills existing rows so this is safe against a non-empty
    # table (autogenerate leaves this out by default, which fails on Postgres).
    op.add_column(
        "inspiration_items",
        sa.Column("already_used", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("inspiration_items", "already_used")
