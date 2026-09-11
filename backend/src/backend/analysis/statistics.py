# app/analysis/statistics.py

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd

from .models import (
    CategoricalStatistics,
    DatetimeStatistics,
    NumericStatistics,
)


class StatisticsEngine:
    """
    Statistical primitives used by the analysis layer.

    This class deliberately has no knowledge of:
    - CSV
    - XLSX
    - PostgreSQL
    - FastAPI
    - Celery
    - RLM
    """

    # --------------------------------------------------------
    # NUMERIC
    # --------------------------------------------------------

    @staticmethod
    def numeric(
        series: pd.Series,
    ) -> NumericStatistics:

        numeric = pd.to_numeric(
            series,
            errors="coerce",
        )

        missing = int(numeric.isna().sum())

        values = numeric.dropna()

        if values.empty:
            return NumericStatistics(
                count=0,
                missing=missing,
            )

        return NumericStatistics(
            count=int(values.count()),
            missing=missing,

            min=float(values.min()),
            max=float(values.max()),

            mean=float(values.mean()),
            median=float(values.median()),

            std=(
                float(values.std())
                if len(values) > 1
                else 0.0
            ),

            variance=(
                float(values.var())
                if len(values) > 1
                else 0.0
            ),

            q1=float(values.quantile(0.25)),
            q3=float(values.quantile(0.75)),

            sum=float(values.sum()),
        )

    # --------------------------------------------------------
    # CATEGORICAL
    # --------------------------------------------------------

    @staticmethod
    def categorical(
        series: pd.Series,
        top_n: int = 20,
    ) -> CategoricalStatistics:

        missing = int(series.isna().sum())

        values = (
            series
            .dropna()
            .astype(str)
        )

        frequencies = (
            values
            .value_counts()
            .head(top_n)
            .to_dict()
        )

        top = None
        top_frequency = 0

        if frequencies:
            top = str(next(iter(frequencies)))
            top_frequency = int(
                frequencies[top]
            )

        return CategoricalStatistics(
            count=int(len(values)),
            missing=missing,
            unique=int(values.nunique()),
            top=top,
            top_frequency=top_frequency,
            frequencies={
                str(k): int(v)
                for k, v in frequencies.items()
            },
        )

    # --------------------------------------------------------
    # DATETIME
    # --------------------------------------------------------

    @staticmethod
    def datetime(
        series: pd.Series,
    ) -> DatetimeStatistics:

        values = pd.to_datetime(
            series,
            errors="coerce",
        )

        missing = int(values.isna().sum())

        valid = values.dropna()

        if valid.empty:
            return DatetimeStatistics(
                count=0,
                missing=missing,
                unique=0,
            )

        min_value = valid.min()
        max_value = valid.max()

        # Convert pandas Timestamp to python datetime.
        min_datetime = min_value.to_pydatetime()
        max_datetime = max_value.to_pydatetime()

        return DatetimeStatistics(
            count=int(valid.count()),
            missing=missing,

            min=min_datetime,
            max=max_datetime,

            unique=int(valid.nunique()),
        )

    # --------------------------------------------------------
    # CORRELATION
    # --------------------------------------------------------

    @staticmethod
    def correlation(
        df: pd.DataFrame,
        method: Literal["pearson", "kendall", "spearman"] = "pearson",
    ) -> dict[str, dict[str, float]]:

        numeric = df.select_dtypes(
            include="number"
        )

        if numeric.empty:
            return {}

        result = numeric.corr(
            method=method
        )

        return {
            str(column): {
                str(other): (
                    float(value)
                    if not pd.isna(value)
                    else float("nan")
                )
                for other, value in row.items()
            }
            for column, row in result.to_dict(
                orient="index"
            ).items()
        }

    # --------------------------------------------------------
    # PERCENTILES
    # --------------------------------------------------------

    @staticmethod
    def percentiles(
        series: pd.Series,
        values: list[float],
    ) -> dict[str, float]:

        numeric = pd.to_numeric(
            series,
            errors="coerce",
        ).dropna()

        if numeric.empty:
            return {}

        result = {}

        for percentile in values:
            result[str(percentile)] = float(
                numeric.quantile(percentile)
            )

        return result

    # --------------------------------------------------------
    # DESCRIPTIVE SUMMARY
    # --------------------------------------------------------

    @staticmethod
    def describe(
        df: pd.DataFrame,
    ) -> dict[str, Any]:

        result: dict[str, Any] = {}

        for column in df.columns:

            series = df[column]

            if pd.api.types.is_numeric_dtype(series):
                stats = StatisticsEngine.numeric(
                    series
                )

            elif pd.api.types.is_datetime64_any_dtype(series):
                stats = StatisticsEngine.datetime(
                    series
                )

            else:
                stats = StatisticsEngine.categorical(
                    series
                )

            result[str(column)] = stats.model_dump()

        return result
