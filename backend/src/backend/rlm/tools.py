from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel

from ..analysis.analyzer import Analyzer
from ..analysis.models import AggregationFunction
from ..analysis.statistics import StatisticsEngine
from ..data_runtime.profiling.profiler import DatasetProfiler
from ..data_runtime.runtime import DataRuntime
from .models import RunCollector


def _serialize(result: Any) -> Any:
    if result is None:
        return None

    if isinstance(result, BaseModel):
        return result.model_dump(mode="json")

    if is_dataclass(result) and not isinstance(result, type):
        return asdict(result)

    if isinstance(result, pd.DataFrame):
        return result.to_dict(orient="records")

    if isinstance(result, (list, tuple)):
        return [_serialize(item) for item in result]

    if isinstance(result, dict):
        return {key: _serialize(value) for key, value in result.items()}

    return result


class AnalysisTools:
    """
    Controlled analytical interface exposed to the RLM.

    The RLM never directly accesses DataRuntime.
    """

    def __init__(self, runtime: DataRuntime):
        self.runtime = runtime
        self.analyzer = Analyzer(runtime)
        self.profiler = DatasetProfiler(runtime)

    async def profile_dataset(self) -> Any:
        return _serialize(await self.profiler.profile())

    async def get_columns(self) -> list[dict[str, Any]]:
        schema = await self.runtime.schema()
        return [
            {
                "name": column.name,
                "dtype": column.dtype,
                "nullable": column.nullable,
            }
            for column in schema.columns
        ]

    async def count(self) -> int:
        schema = await self.runtime.schema()
        if schema.row_count is not None:
            return schema.row_count

        df = await self.analyzer.dataframe()
        return len(df)

    async def sample(self, n: int = 10) -> Any:
        return await self.analyzer.sample(n=n)

    async def value_counts(
        self,
        column: str,
        limit: int = 20,
    ) -> Any:
        df = await self.analyzer.dataframe()
        if column not in df.columns:
            raise ValueError(f"Unknown column: {column}")

        stats = StatisticsEngine.categorical(
            df[column],
            top_n=limit,
        )
        return _serialize(stats)

    async def describe(self) -> Any:
        return await self.analyzer.describe()

    async def describe_column(self, column: str) -> Any:
        result = await self.analyzer.analyze()
        for col in result.columns:
            if col.column == column:
                return _serialize(col)

        raise ValueError(f"Unknown column: {column}")

    async def filter_rows(
        self,
        expression: str,
        limit: int = 100,
    ) -> Any:
        rows = await self.analyzer.filter(expression)
        return rows[:limit]

    async def analyze(self) -> Any:
        return _serialize(await self.analyzer.analyze())

    async def quality_report(self) -> Any:
        return _serialize(await self.analyzer.quality_report())

    async def correlation(
        self,
        method: Literal["pearson", "kendall", "spearman"] = "pearson",
    ) -> Any:
        return await self.analyzer.correlation(method=method)

    async def percentiles(
        self,
        column: str,
        values: list[float],
    ) -> Any:
        return await self.analyzer.percentiles(column, values)

    async def aggregate(
        self,
        group_by: str | list[str],
        aggregations: dict[str, list[AggregationFunction]],
    ) -> Any:
        return _serialize(
            await self.analyzer.aggregate(
                group_by=group_by,
                aggregations=aggregations,
            )
        )

    async def timeseries(
        self,
        date_column: str,
        value_column: str,
        frequency: str = "D",
        aggregation: str = "sum",
    ) -> Any:
        return _serialize(
            await self.analyzer.timeseries(
                date_column=date_column,
                value_column=value_column,
                frequency=frequency,
                aggregation=aggregation,
            )
        )

    async def detect_anomalies(
        self,
        column: str,
        method: str = "zscore",
        threshold: float = 3.0,
    ) -> Any:
        return _serialize(
            await self.analyzer.detect_anomalies(
                column=column,
                method=method,
                threshold=threshold,
            )
        )


class ToolRegistry:
    def __init__(
        self,
        tools: AnalysisTools,
        collector: RunCollector | None = None,
    ):
        self.tools = tools
        self.collector = collector

    def bind_collector(self, collector: RunCollector) -> None:
        self.collector = collector

    def _wrap(self, name: str, fn: Any) -> Any:
        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            if self.collector is not None:
                self.collector.record_tool_call(name)
            return await fn(*args, **kwargs)

        wrapped.__name__ = name
        return wrapped

    def namespace(self) -> dict[str, Any]:
        raw = {
            "profile_dataset": self.tools.profile_dataset,
            "get_columns": self.tools.get_columns,
            "count": self.tools.count,
            "sample": self.tools.sample,
            "value_counts": self.tools.value_counts,
            "describe": self.tools.describe,
            "describe_column": self.tools.describe_column,
            "filter_rows": self.tools.filter_rows,
            "analyze": self.tools.analyze,
            "quality_report": self.tools.quality_report,
            "correlation": self.tools.correlation,
            "percentiles": self.tools.percentiles,
            "aggregate": self.tools.aggregate,
            "timeseries": self.tools.timeseries,
            "detect_anomalies": self.tools.detect_anomalies,
        }
        return {name: self._wrap(name, fn) for name, fn in raw.items()}
