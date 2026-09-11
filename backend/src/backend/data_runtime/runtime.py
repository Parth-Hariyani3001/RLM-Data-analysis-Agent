# app/data_runtime/runtime.py

from __future__ import annotations

import re

import pandas as pd

from .base import DataSource
from .exceptions import QueryValidationError
from .models import (
    DatasetSample,
    DatasetSchema,
    QueryResult,
)


FORBIDDEN_SQL = {
    "DROP",
    "DELETE",
    "TRUNCATE",
    "ALTER",
    "UPDATE",
    "INSERT",
    "CREATE",
    "GRANT",
    "REVOKE",
}


class DataRuntime:
    def __init__(
        self,
        source: DataSource,
        max_query_rows: int = 10_000,
    ):
        self.source = source
        self.max_query_rows = max_query_rows

    async def connect(self) -> None:
        await self.source.connect()

    async def schema(self) -> DatasetSchema:
        return await self.source.schema()

    async def sample(
        self,
        limit: int = 10,
    ) -> DatasetSample:
        limit = min(
            max(limit, 1),
            100,
        )

        return await self.source.sample(limit)

    async def query(
        self,
        sql: str,
        limit: int | None = None,
    ) -> QueryResult:
        self._validate_sql(sql)

        effective_limit = min(
            limit or self.max_query_rows,
            self.max_query_rows,
        )

        return await self.source.query(
            sql,
            limit=effective_limit,
        )

    def _validate_sql(self, sql: str) -> None:
        normalized = re.sub(
            r"\s+",
            " ",
            sql.strip().upper(),
        )

        if not normalized:
            raise QueryValidationError(
                "SQL query cannot be empty"
            )

        if not (
            normalized.startswith("SELECT")
            or normalized.startswith("WITH")
        ):
            raise QueryValidationError(
                "Only SELECT/WITH queries are allowed"
            )

        for keyword in FORBIDDEN_SQL:
            pattern = rf"\b{keyword}\b"

            if re.search(pattern, normalized):
                raise QueryValidationError(
                    f"Forbidden SQL operation: {keyword}"
                )

    async def to_dataframe(self) -> pd.DataFrame:
        result = await self.query("SELECT * FROM data")
        return pd.DataFrame(result.rows, columns=result.columns)

    async def close(self) -> None:
        await self.source.close()
