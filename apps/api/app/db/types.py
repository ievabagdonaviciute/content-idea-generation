"""Dialect-aware column types.

``Vector`` stores an embedding as a real ``pgvector`` column on PostgreSQL and as a
JSON-encoded ``Text`` column everywhere else (SQLite, used for the test suite and
sandbox development where a local Postgres instance is not available -- see
docs/ARCHITECTURE.md for why). Application code always works with
``list[float] | None`` regardless of dialect.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator


class Vector(TypeDecorator[list[float]]):
    impl = Text
    cache_ok = True

    def __init__(self, dim: int, *args: Any, **kwargs: Any) -> None:
        self.dim = dim
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            from pgvector.sqlalchemy import Vector as PgVector

            return dialect.type_descriptor(PgVector(self.dim))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: list[float] | None, dialect: Any) -> Any:
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return json.dumps(value)

    def process_result_value(self, value: Any, dialect: Any) -> list[float] | None:
        if value is None:
            return None
        if dialect.name == "postgresql":
            return list(value)
        return json.loads(value)
