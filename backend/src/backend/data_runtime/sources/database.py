# app/data_runtime/sources/database.py

from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
)

from ..base import DataSource
from ..models import (
    ColumnInfo,
    DatasetSample,
    DatasetSchema,
    QueryResult,
)


class DatabaseSource(DataSource):

    def __init__(
        self,
        connection_url: str,
        table_name: str,
    ):
        self.connection_url = connection_url
        self.table_name = table_name

        self.engine: AsyncEngine | None = None

    async def connect(self) -> None:
        self.engine = create_async_engine(
            self.connection_url,
            pool_pre_ping=True,
        )

    def _ensure_engine(self) -> AsyncEngine:
        if self.engine is None:
            raise RuntimeError(
                "Database source is not connected"
            )

        return self.engine

    async def query(
        self,
        sql: str,
        limit: int | None = None,
    ) -> QueryResult:
        engine = self._ensure_engine()

        if limit is not None:
            sql = f"""
            SELECT *
            FROM (
                {sql}
            ) AS runtime_query
            LIMIT {int(limit)}
            """

        async with engine.connect() as connection:
            result = await connection.execute(
                text(sql)
            )

            rows = result.mappings().all()

            rows = [
                dict(row)
                for row in rows
            ]

            columns = list(
                rows[0].keys()
            ) if rows else []

            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
            )

    async def schema(self) -> DatasetSchema:
        engine = self._ensure_engine()

        # This implementation targets PostgreSQL.
        query = text(
            """
            SELECT
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position
            """
        )

        async with engine.connect() as connection:
            result = await connection.execute(
                query,
                {
                    "table_name": self.table_name,
                },
            )

            rows = result.mappings().all()

            columns = [
                ColumnInfo(
                    name=row["column_name"],
                    dtype=row["data_type"],
                    nullable=row["is_nullable"] == "YES",
                )
                for row in rows
            ]

        count_result = await self.query(
            f'''
            SELECT COUNT(*) AS count
            FROM "{self.table_name}"
            '''
        )

        row_count = (
            count_result.rows[0]["count"]
            if count_result.rows
            else 0
        )

        return DatasetSchema(
            name=self.table_name,
            row_count=row_count,
            columns=columns,
        )

    async def sample(
        self,
        limit: int = 10,
    ) -> DatasetSample:
        result = await self.query(
            f'''
            SELECT *
            FROM "{self.table_name}"
            LIMIT {int(limit)}
            ''',
            limit=limit,
        )

        return DatasetSample(
            columns=result.columns,
            rows=result.rows,
        )

    async def close(self) -> None:
        if self.engine is not None:
            await self.engine.dispose()
            self.engine = None
