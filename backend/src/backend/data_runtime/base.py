# app/data_runtime/base.py

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import (
    DatasetSample,
    DatasetSchema,
    QueryResult,
)


class DataSource(ABC):
    """
    Abstract data source.

    Implementations can represent:
    - CSV
    - XLSX
    - databases
    - future sources
    """

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def schema(self) -> DatasetSchema:
        pass

    @abstractmethod
    async def sample(self, limit: int = 10) -> DatasetSample:
        pass

    @abstractmethod
    async def query(
        self,
        sql: str,
        limit: int | None = None,
    ) -> QueryResult:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass
