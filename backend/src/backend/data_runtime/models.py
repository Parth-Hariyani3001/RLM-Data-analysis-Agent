# app/data_runtime/models.py

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DataSourceType(str, Enum):
    CSV = "csv"
    XLSX = "xlsx"
    DATABASE = "database"


@dataclass
class ColumnInfo:
    name: str
    dtype: str
    nullable: bool = True
    unique_count: int | None = None
    null_count: int | None = None


@dataclass
class DatasetSchema:
    name: str
    row_count: int | None
    columns: list[ColumnInfo] = field(default_factory=list)


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    truncated: bool = False


@dataclass
class DatasetSample:
    columns: list[str]
    rows: list[dict[str, Any]]


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    null_count: int
    null_percentage: float
    unique_count: int | None
    min_value: Any = None
    max_value: Any = None
    mean: float | None = None


@dataclass
class DatasetProfile:
    dataset_name: str
    row_count: int
    column_count: int
    columns: list[ColumnProfile]
