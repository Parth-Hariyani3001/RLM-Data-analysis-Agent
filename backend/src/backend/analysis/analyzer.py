# app/analysis/analyzer.py

from __future__ import annotations

from typing import Any, Literal

import pandas as pd

from ..data_runtime.runtime import DataRuntime

from .aggregations import AggregationEngine
from .anomaly import AnomalyDetector
from .data_quality import DataQualityAnalyzer
from .models import (
    AnalysisResult,
    ColumnAnalysis,
    AggregationFunction,
)
from .statistics import StatisticsEngine
from .timeseries import TimeSeriesAnalyzer


class Analyzer:
    """
    High-level analysis interface.

    The Analyzer knows about DataRuntime but does not know
    where the data originally came from.
    """

    def __init__(
        self,
        runtime: DataRuntime,
    ) -> None:
        self.runtime = runtime

    async def dataframe(
        self,
    ) -> pd.DataFrame:
        return await self.runtime.to_dataframe()

    # ========================================================
    # COMPLETE ANALYSIS
    # ========================================================
    async def analyze(
        self,
    ) -> AnalysisResult:
        df = await self.dataframe()
        columns = []
        for column in df.columns:
            series = df[column]
            dtype = self._infer_dtype(
                series
            )

            analysis = ColumnAnalysis(
                column=str(column),
                dtype=dtype,
            )

            if dtype == "numeric":
                analysis.numeric = (
                    StatisticsEngine.numeric(
                        series
                    )
                )

            elif dtype == "datetime":
                analysis.datetime = (
                    StatisticsEngine.datetime(
                        series
                    )
                )

            else:
                analysis.categorical = (
                    StatisticsEngine.categorical(
                        series
                    )
                )

            columns.append(
                analysis
            )

        quality = (
            DataQualityAnalyzer.analyze(
                df
            )
        )

        dataset_id = getattr(
            self.runtime,
            "dataset_id",
            None,
        )

        return AnalysisResult(
            dataset_id=dataset_id,
            row_count=len(df),
            column_count=len(df.columns),
            columns=columns,
            quality=quality,
        )

    # ========================================================
    # STATISTICS
    # ========================================================

    async def describe(
        self,
    ) -> dict[str, Any]:

        df = await self.dataframe()

        return StatisticsEngine.describe(
            df
        )

    async def correlation(
        self,
        method: Literal["pearson", "kendall", "spearman"] = "pearson",
    ) -> dict[str, dict[str, float]]:

        df = await self.dataframe()

        return StatisticsEngine.correlation(
            df,
            method=method,
        )

    async def percentiles(
        self,
        column: str,
        values: list[float],
    ) -> dict[str, float]:

        df = await self.dataframe()

        self._require_column(
            df,
            column,
        )

        return StatisticsEngine.percentiles(
            df[column],
            values,
        )

    # ========================================================
    # DATA QUALITY
    # ========================================================

    async def quality_report(self):

        df = await self.dataframe()

        return DataQualityAnalyzer.analyze(
            df
        )

    # ========================================================
    # AGGREGATIONS
    # ========================================================

    async def aggregate(
        self,
        group_by: str | list[str],
        aggregations: dict[
            str,
            list[AggregationFunction],
        ],
    ):

        df = await self.dataframe()

        return AggregationEngine.aggregate(
            df=df,
            group_by=group_by,
            aggregations=aggregations,
        )

    # ========================================================
    # TIME SERIES
    # ========================================================

    async def timeseries(
        self,
        date_column: str,
        value_column: str,
        frequency: str = "D",
        aggregation: str = "sum",
    ):

        df = await self.dataframe()

        return TimeSeriesAnalyzer.aggregate(
            df=df,
            date_column=date_column,
            value_column=value_column,
            frequency=frequency,
            aggregation=aggregation,
        )

    # ========================================================
    # ANOMALIES
    # ========================================================

    async def detect_anomalies(
        self,
        column: str,
        method: str = "zscore",
        threshold: float = 3.0,
    ):

        df = await self.dataframe()

        if method == "zscore":

            return AnomalyDetector.zscore(
                df,
                column,
                threshold,
            )

        if method == "iqr":

            return AnomalyDetector.iqr(
                df,
                column,
                threshold,
            )

        raise ValueError(
            f"Unsupported anomaly method: "
            f"{method}"
        )

    # ========================================================
    # FILTERING
    # ========================================================

    async def filter(
        self,
        expression: str,
    ) -> list[dict[str, Any]]:
        """
        Filter rows using a pandas expression.

        Example:

            revenue > 1000 and country == 'India'

        This method should eventually be replaced/guarded
        when exposed to an LLM.
        """

        df = await self.dataframe()

        result = df.query(
            expression
        )

        return self._serialize_dataframe(
            result
        )

    # ========================================================
    # SAMPLE
    # ========================================================

    async def sample(
        self,
        n: int = 10,
        random_state: int | None = None,
    ) -> list[dict[str, Any]]:

        df = await self.dataframe()

        n = min(
            max(n, 0),
            len(df),
        )

        result = df.sample(
            n=n,
            random_state=random_state,
        )

        return self._serialize_dataframe(
            result
        )

    # ========================================================
    # INTERNAL HELPERS
    # ========================================================

    @staticmethod
    def _infer_dtype(
        series: pd.Series,
    ) -> str:

        if pd.api.types.is_bool_dtype(series):
            return "boolean"

        if pd.api.types.is_numeric_dtype(series):
            return "numeric"

        if pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"

        # Attempt datetime inference for object columns.
        if series.dtype == "object":

            parsed = pd.to_datetime(
                series,
                errors="coerce",
            )

            non_null = series.notna().sum()

            if (
                non_null > 0
                and parsed.notna().sum()
                / non_null
                >= 0.9
            ):
                return "datetime"

        return "categorical"

    @staticmethod
    def _require_column(
        df: pd.DataFrame,
        column: str,
    ) -> None:

        if column not in df.columns:
            raise ValueError(
                f"Unknown column: {column}"
            )

    @staticmethod
    def _serialize_dataframe(
        df: pd.DataFrame,
    ) -> list[dict[str, Any]]:

        data = df.copy()

        data = data.replace(
            {
                float("inf"): None,
                float("-inf"): None,
            }
        )

        data = data.where(
            pd.notna(data),
            None,
        )

        records = data.to_dict(
            orient="records"
        )

        # Convert pandas-specific scalar values.
        output = []

        for record in records:

            clean = {}

            for key, value in record.items():

                if hasattr(
                    value,
                    "item",
                ):
                    try:
                        value = value.item()
                    except (ValueError, TypeError):
                        pass

                if isinstance(
                    value,
                    pd.Timestamp,
                ):
                    value = value.to_pydatetime()

                clean[str(key)] = value

            output.append(clean)

        return output
