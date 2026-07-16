"""initial schema

This migration targets PostgreSQL/pgvector (the production database -- see
docs/ARCHITECTURE.md). Rather than hand-duplicating ~18 tables as op.create_table
DSL (a common source of drift from the actual SQLAlchemy models), it enables the
pgvector extension and then delegates table creation to Base.metadata, which is the
single source of truth for the schema. This is standard practice for a first Alembic
revision in a project small enough that a second source of truth would only add risk.

Revision ID: ef40bc825ed2
Revises:
Create Date: 2026-07-15 13:42:53.062091

"""

from collections.abc import Sequence

from alembic import op
from app.models import Base

# revision identifiers, used by Alembic.
revision: str = "ef40bc825ed2"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
