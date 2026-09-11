# app/data_runtime/sources/excel.py

from __future__ import annotations

from pathlib import Path

from ..base import DataSource
from ..engines.duck_db import DuckDBEngine
from ..models import (
    DatasetSample,
    DatasetSchema,
    QueryResult,
)


class ExcelSource(DataSource):

    def __init__(
        self,
        path: str,
        table_name: str = "data",
        sheet_name: str | None = None,
        engine: DuckDBEngine | None = None,
    ):
        self.path = Path(path)
        self.table_name = table_name
        self.sheet_name = sheet_name
        self.engine = engine or DuckDBEngine()

    async def connect(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(
                f"Excel file not found: {self.path}"
            )

        await self.engine.connect()

        await self.engine.register_excel(
            table_name=self.table_name,
            path=str(self.path),
            sheet_name=self.sheet_name,
        )

    async def schema(self) -> DatasetSchema:
        return await self.engine.schema(
            self.table_name
        )

    async def sample(
        self,
        limit: int = 10,
    ) -> DatasetSample:
        return await self.engine.sample(
            self.table_name,
            limit,
        )

    async def query(
        self,
        sql: str,
        limit: int | None = None,
    ) -> QueryResult:
        return await self.engine.execute(
            sql,
            limit,
        )

    async def close(self) -> None:
        await self.engine.close()
