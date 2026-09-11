# app/analysis/models.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ============================================================
# BASIC
# ============================================================

class NumericStatistics(BaseModel):
    count: int
    missing: int

    min: float | None = None
    max: float | None = None

    mean: float | None = None
    median: float | None = None

    std: float | None = None
    variance: float | None = None

    q1: float | None = None
    q3: float | None = None

    sum: float | None = None


class CategoricalStatistics(BaseModel):
    count: int
    missing: int
    unique: int

    top: str | None = None
    top_frequency: int = 0

    frequencies: dict[str, int] = Field(default_factory=dict)


class DatetimeStatistics(BaseModel):
    count: int
    missing: int

    min: datetime | None = None
    max: datetime | None = None

    unique: int


# ============================================================
# DATA QUALITY
# ============================================================

class ColumnQuality(BaseModel):
    column: str

    total: int
    missing: int
    missing_percentage: float

    unique: int
    duplicate_percentage: float

    inferred_type: str

    null_values: int = 0


class DuplicateInfo(BaseModel):
    duplicate_rows: int
    duplicate_percentage: float


class DataQualityReport(BaseModel):
    row_count: int
    column_count: int

    duplicate_rows: int
    duplicate_percentage: float

    missing_cells: int
    missing_percentage: float

    columns: list[ColumnQuality]


# ============================================================
# AGGREGATION
# ============================================================

AggregationFunction = Literal[
    "sum",
    "mean",
    "median",
    "min",
    "max",
    "count",
    "nunique",
    "std",
]


class AggregationResult(BaseModel):
    group_by: list[str]

    aggregations: dict[str, list[AggregationFunction]]

    rows: list[dict[str, Any]]

    row_count: int


# ============================================================
# TIME SERIES
# ============================================================

TimeFrequency = Literal[
    "D",
    "W",
    "M",
    "ME",
    "Q",
    "QE",
    "Y",
    "YE",
    "A",
    "h",
    "min",
]


class TimeSeriesPoint(BaseModel):
    timestamp: datetime
    value: float


class TimeSeriesResult(BaseModel):
    date_column: str
    value_column: str
    frequency: str

    points: list[TimeSeriesPoint]

    count: int


# ============================================================
# ANOMALIES
# ============================================================

AnomalyMethod = Literal[
    "zscore",
    "iqr",
]


class Anomaly(BaseModel):
    row_index: int

    value: float

    score: float

    method: AnomalyMethod


class AnomalyResult(BaseModel):
    column: str
    method: AnomalyMethod

    threshold: float

    anomalies: list[Anomaly]

    total_anomalies: int


# ============================================================
# ANALYSIS RESPONSE
# ============================================================

class ColumnAnalysis(BaseModel):
    column: str
    dtype: str

    numeric: NumericStatistics | None = None
    categorical: CategoricalStatistics | None = None
    datetime: DatetimeStatistics | None = None


class AnalysisResult(BaseModel):
    dataset_id: str | None = None

    row_count: int
    column_count: int

    columns: list[ColumnAnalysis]

    quality: DataQualityReport
