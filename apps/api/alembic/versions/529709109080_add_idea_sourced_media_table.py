"""add idea_sourced_media table

Revision ID: 529709109080
Revises: fe7d1be49fe7
Create Date: 2026-07-27 21:17:40.010174

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "529709109080"
down_revision: str | Sequence[str] | None = "fe7d1be49fe7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "idea_sourced_media",
        sa.Column("idea_id", sa.Uuid(), nullable=False),
        sa.Column("images", sa.JSON(), nullable=False),
        sa.Column("memes", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["idea_id"], ["content_ideas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idea_id"),
    )


def downgrade() -> None:
    op.drop_table("idea_sourced_media")
