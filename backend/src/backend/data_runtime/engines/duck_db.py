# app/data_runtime/engines/duckdb.py

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import duckdb

from ..csv_encoding import duckdb_read_csv_options
from ..exceptions import QueryError
from ..models import (
    ColumnInfo,
    DatasetSample,
    DatasetSchema,
    QueryResult,
)


class DuckDBEngine:
    """
    Analytical execution engine.

    DuckDB is used because it is particularly well suited
    for analytical queries over local files and tabular data.
    """

    def __init__(
        self,
        database: str = ":memory:",
        max_rows: int = 10_000,
    ):
        self.database = database
        self.max_rows = max_rows
        self.connection: duckdb.DuckDBPyConnection | None = None

    async def connect(self) -> None:
        await asyncio.to_thread(self._connect)

    def _connect(self) -> None:
        self.connection = duckdb.connect(self.database)

        # Conservative defaults.
        self.connection.execute(
            "SET threads = 4"
        )

    def _ensure_connection(self) -> duckdb.DuckDBPyConnection:
        if self.connection is None:
            raise RuntimeError("DuckDB connection is not initialized")

        return self.connection

    async def execute(
        self,
        sql: str,
        limit: int | None = None,
    ) -> QueryResult:
        return await asyncio.to_thread(
            self._execute,
            sql,
            limit,
        )

    def _execute(
        self,
        sql: str,
        limit: int | None = None,
    ) -> QueryResult:
        connection = self._ensure_connection()

        try:
            cursor = connection.execute(sql)
            columns = [
                description[0]
                for description in cursor.description or []
            ]

            effective_limit = limit or self.max_rows
            rows = cursor.fetchmany(effective_limit + 1)

            truncated = len(rows) > effective_limit

            if truncated:
                rows = rows[:effective_limit]

            result_rows: list[dict[str, Any]] = [
                dict(zip(columns, row))
                for row in rows
            ]

            return QueryResult(
                columns=columns,
                rows=result_rows,
                row_count=len(result_rows),
                truncated=truncated,
            )

        except Exception as exc:
            raise QueryError(
                f"Failed to execute query: {exc}"
            ) from exc

    async def register_csv(
        self,
        table_name: str,
        path: str,
    ) -> None:
        await asyncio.to_thread(
            self._register_csv,
            table_name,
            path,
        )

    def _register_csv(
        self,
        table_name: str,
        path: str,
    ) -> None:
        connection = self._ensure_connection()
        resolved_path = Path(path).resolve()
        escaped_path = str(resolved_path).replace("'", "''")
        read_options = duckdb_read_csv_options(resolved_path)
        connection.execute(
            f"""
            CREATE OR REPLACE TABLE "{table_name}" AS
            SELECT *
            FROM read_csv(
                '{escaped_path}',
                {read_options}
            )
            """
        )

    async def register_excel(
        self,
        table_name: str,
        path: str,
        sheet_name: str | None = None,
    ) -> None:
        await asyncio.to_thread(
            self._register_excel,
            table_name,
            path,
            sheet_name,
        )

    def _register_excel(
        self,
        table_name: str,
        path: str,
        sheet_name: str | None,
    ) -> None:
        connection = self._ensure_connection()
        import pandas as pd
        dataframe = pd.read_excel(
            path,
            sheet_name=sheet_name or 0,
        )

        connection.register(
            f"{table_name}_df",
            dataframe,
        )

        connection.execute(
            f"""
            CREATE OR REPLACE VIEW "{table_name}"
            AS
            SELECT *
            FROM "{table_name}_df"
            """
        )

    async def schema(
        self,
        table_name: str,
    ) -> DatasetSchema:
        result = await self.execute(
            f'DESCRIBE "{table_name}"'
        )

        columns = [
            ColumnInfo(
                name=row["column_name"],
                dtype=row["column_type"],
                nullable=row.get("null") != "NO",
            )
            for row in result.rows
        ]

        count_result = await self.execute(
            f'SELECT COUNT(*) AS count FROM "{table_name}"',
            limit=1,
        )

        row_count = (
            count_result.rows[0]["count"]
            if count_result.rows
            else 0
        )

        return DatasetSchema(
            name=table_name,
            row_count=row_count,
            columns=columns,
        )

    async def sample(
        self,
        table_name: str,
        limit: int = 10,
    ) -> DatasetSample:
        result = await self.execute(
            f'''
            SELECT *
            FROM "{table_name}"
            LIMIT {int(limit)}
            ''',
            limit=limit,
        )

        return DatasetSample(
            columns=result.columns,
            rows=result.rows,
        )

    async def close(self) -> None:
        if self.connection is not None:
            await asyncio.to_thread(
                self.connection.close
            )

            self.connection = None
