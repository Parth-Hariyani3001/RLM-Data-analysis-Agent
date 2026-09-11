# app/analysis/timeseries.py

from __future__ import annotations

from typing import cast
import pandas as pd

from .models import (
    TimeSeriesPoint,
    TimeSeriesResult,
)


class TimeSeriesAnalyzer:

    SUPPORTED_FREQUENCIES = {
        "min",
        "h",
        "D",
        "W",
        "M",
        "ME",
        "Q",
        "QE",
        "Y",
        "YE",
        "A",
    }

    FREQUENCY_ALIASES: dict[str, str] = {
        "M": "ME",
        "Q": "QE",
        "Y": "YE",
        "A": "YE",
    }

    @classmethod
    def aggregate(
        cls,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
        frequency: str = "D",
        aggregation: str = "sum",
    ) -> TimeSeriesResult:

        cls._validate(
            df,
            date_column,
            value_column,
            frequency,
        )

        pandas_freq = cls._normalize_frequency(frequency)

        data = df[
            [
                date_column,
                value_column,
            ]
        ].copy()

        data[date_column] = pd.to_datetime(
            data[date_column],
            errors="coerce",
        )

        data[value_column] = pd.to_numeric(
            data[value_column],
            errors="coerce",
        )

        data = data.dropna(
            subset=[
                date_column,
                value_column,
            ]
        )

        if data.empty:
            return TimeSeriesResult(
                date_column=date_column,
                value_column=value_column,
                frequency=pandas_freq,
                points=[],
                count=0,
            )

        data = data.set_index(
            date_column
        )

        if aggregation == "sum":
            result = data[value_column].resample(
                pandas_freq
            ).sum()

        elif aggregation == "mean":
            result = data[value_column].resample(
                pandas_freq
            ).mean()

        elif aggregation == "median":
            result = data[value_column].resample(
                pandas_freq
            ).median()

        elif aggregation == "min":
            result = data[value_column].resample(
                pandas_freq
            ).min()

        elif aggregation == "max":
            result = data[value_column].resample(
                pandas_freq
            ).max()

        elif aggregation == "count":
            result = data[value_column].resample(
                pandas_freq
            ).count()

        else:
            raise ValueError(
                f"Unsupported aggregation: "
                f"{aggregation}"
            )

        points = []

        for timestamp, value in result.items():

            if pd.isna(value):
                continue

            points.append(
                TimeSeriesPoint(
                    timestamp=cast(pd.Timestamp, timestamp).to_pydatetime(),
                    value=float(value),
                )
            )

        return TimeSeriesResult(
            date_column=date_column,
            value_column=value_column,
            frequency=pandas_freq,
            points=points,
            count=len(points),
        )

    @classmethod
    def _normalize_frequency(cls, frequency: str) -> str:
        return cls.FREQUENCY_ALIASES.get(frequency, frequency)

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    @classmethod
    def _validate(
        cls,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
        frequency: str,
    ) -> None:

        if date_column not in df.columns:
            raise ValueError(
                f"Unknown date column: "
                f"{date_column}"
            )

        if value_column not in df.columns:
            raise ValueError(
                f"Unknown value column: "
                f"{value_column}"
            )

        if frequency not in cls.SUPPORTED_FREQUENCIES:
            raise ValueError(
                f"Unsupported frequency "
                f"'{frequency}'. Supported: "
                f"{sorted(cls.SUPPORTED_FREQUENCIES)}"
            )
