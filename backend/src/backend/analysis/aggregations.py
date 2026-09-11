from __future__ import annotations

from typing import Any

import pandas as pd

from .models import (
    AggregationFunction,
    AggregationResult,
)


class AggregationEngine:
    SUPPORTED_FUNCTIONS = {
        "sum",
        "mean",
        "median",
        "min",
        "max",
        "count",
        "nunique",
        "std",
    }

    @staticmethod
    def _normalize_group_by(
        group_by: str | list[str],
    ) -> list[str]:
        if isinstance(group_by, str):
            return [group_by]

        return list(group_by)

    @classmethod
    def aggregate(
        cls,
        df: pd.DataFrame,
        group_by: str | list[str],
        aggregations: dict[
            str,
            AggregationFunction | list[AggregationFunction],
        ],
    ) -> AggregationResult:

        group_by = cls._normalize_group_by(group_by)

        # Normalize:
        #
        # {"SALES": "sum"}
        #
        # into:
        #
        # {"SALES": ["sum"]}
        normalized_aggregations: dict[
            str,
            list[AggregationFunction],
        ] = {
            column: (
                functions
                if isinstance(functions, list)
                else [functions]
            )
            for column, functions in aggregations.items()
        }

        cls._validate_columns(
            df,
            group_by,
            normalized_aggregations,
        )

        cls._validate_functions(
            normalized_aggregations
        )

        pandas_agg: dict[str, list[str]] = {
            column: list(functions)
            for column, functions
            in normalized_aggregations.items()
        }

        if group_by:
            grouped = (
                df
                .groupby(
                    group_by,
                    dropna=False,
                )
                .agg(pandas_agg)
            )

            grouped = grouped.reset_index()

            def _flatten(col: object) -> str:
                if isinstance(col, tuple):
                    return "_".join(
                        str(part)
                        for part in col
                        if str(part) != ""
                    )

                return str(col)

            result = grouped.copy()
            result.columns = result.columns.map(_flatten)

        else:
            result = (
                df
                .agg(pandas_agg)
                .to_frame()
                .T
            )

        result = result.replace(
            {
                float("inf"): None,
                float("-inf"): None,
            }
        )

        result = result.astype(object)

        result = result.where(
            pd.notna(result),
            None,
        )

        rows: list[dict[str, Any]] = [
            {
                str(k): v
                for k, v in row.items()
            }
            for row in result.to_dict(
                orient="records"
            )
        ]

        return AggregationResult(
            group_by=group_by,
            aggregations=normalized_aggregations,
            rows=rows,
            row_count=len(rows),
        )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    @staticmethod
    def _validate_columns(
        df: pd.DataFrame,
        group_by: list[str],
        aggregations: dict[
            str,
            list[AggregationFunction],
        ],
    ) -> None:

        columns = set(df.columns)

        requested = (
            set(group_by)
            | set(aggregations.keys())
        )

        missing = requested - columns

        if missing:
            raise ValueError(
                "Unknown columns: "
                + ", ".join(
                    sorted(missing)
                )
            )

    @classmethod
    def _validate_functions(
        cls,
        aggregations: dict[
            str,
            list[AggregationFunction],
        ],
    ) -> None:

        for column, functions in aggregations.items():
            for function in functions:
                if function not in cls.SUPPORTED_FUNCTIONS:
                    raise ValueError(
                        f"Unsupported aggregation "
                        f"'{function}' for column "
                        f"'{column}'. Supported: "
                        f"{sorted(cls.SUPPORTED_FUNCTIONS)}"
                    )
