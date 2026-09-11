# app/analysis/data_quality.py

from __future__ import annotations

import pandas as pd

from .models import (
    ColumnQuality,
    DataQualityReport,
    DuplicateInfo,
)


class DataQualityAnalyzer:

    # --------------------------------------------------------
    # DUPLICATES
    # --------------------------------------------------------

    @staticmethod
    def duplicates(
        df: pd.DataFrame,
    ) -> DuplicateInfo:

        row_count = len(df)

        if row_count == 0:
            return DuplicateInfo(
                duplicate_rows=0,
                duplicate_percentage=0.0,
            )

        duplicate_rows = int(
            df.duplicated()
            .sum()
        )

        percentage = (
            duplicate_rows
            / row_count
            * 100
        )

        return DuplicateInfo(
            duplicate_rows=duplicate_rows,
            duplicate_percentage=percentage,
        )

    # --------------------------------------------------------
    # COLUMN QUALITY
    # --------------------------------------------------------

    @staticmethod
    def column_quality(
        df: pd.DataFrame,
        column: str,
    ) -> ColumnQuality:

        series = df[column]

        total = len(series)

        missing = int(
            series.isna().sum()
        )

        unique = int(
            series.nunique(
                dropna=True
            )
        )

        missing_percentage = (
            missing / total * 100
            if total
            else 0.0
        )

        duplicate_percentage = (
            (total - unique - missing)
            / total
            * 100
            if total
            else 0.0
        )

        if pd.api.types.is_numeric_dtype(series):
            inferred_type = "numeric"

        elif pd.api.types.is_datetime64_any_dtype(series):
            inferred_type = "datetime"

        elif pd.api.types.is_bool_dtype(series):
            inferred_type = "boolean"

        else:
            inferred_type = "categorical"

        return ColumnQuality(
            column=column,

            total=total,
            missing=missing,

            missing_percentage=missing_percentage,

            unique=unique,
            duplicate_percentage=max(
                0.0,
                duplicate_percentage,
            ),

            inferred_type=inferred_type,

            null_values=missing,
        )

    # --------------------------------------------------------
    # FULL QUALITY REPORT
    # --------------------------------------------------------

    @staticmethod
    def analyze(
        df: pd.DataFrame,
    ) -> DataQualityReport:

        row_count = len(df)
        column_count = len(df.columns)

        duplicate_info = (
            DataQualityAnalyzer
            .duplicates(df)
        )

        missing_cells = int(
            df.isna()
            .sum()
            .sum()
        )

        total_cells = (
            row_count
            * column_count
        )

        missing_percentage = (
            missing_cells
            / total_cells
            * 100
            if total_cells
            else 0.0
        )

        columns = [
            DataQualityAnalyzer.column_quality(
                df,
                column,
            )
            for column in df.columns
        ]

        return DataQualityReport(
            row_count=row_count,
            column_count=column_count,
            duplicate_rows=(
                duplicate_info.duplicate_rows
            ),
            duplicate_percentage=(
                duplicate_info
                .duplicate_percentage
            ),
            missing_cells=missing_cells,
            missing_percentage=missing_percentage,
            columns=columns,
        )
