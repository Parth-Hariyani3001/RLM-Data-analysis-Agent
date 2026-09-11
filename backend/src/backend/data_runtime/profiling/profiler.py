from __future__ import annotations

from typing import Any

from ..models import ColumnProfile, DatasetProfile
from ..runtime import DataRuntime


NUMERIC_TYPES = {
    "TINYINT",
    "SMALLINT",
    "INTEGER",
    "BIGINT",
    "HUGEINT",
    "FLOAT",
    "DOUBLE",
    "DECIMAL",
}


class DatasetProfiler:
    def __init__(self, runtime: DataRuntime):
        self.runtime = runtime

    async def profile(self) -> DatasetProfile:
        schema = await self.runtime.schema()

        profiles: list[ColumnProfile] = []

        for column in schema.columns:
            name = column.name

            # Quote identifiers safely.
            quoted_name = (
                '"'
                + name.replace('"', '""')
                + '"'
            )

            # Only calculate AVG for numeric columns.
            if column.dtype.upper() in NUMERIC_TYPES:
                mean_expression = f"""
                    AVG({quoted_name}) AS mean_value
                """
            else:
                mean_expression = """
                    NULL AS mean_value
                """

            sql = f"""
                SELECT
                    COUNT(*) AS total_count,
                    COUNT({quoted_name}) AS non_null_count,
                    COUNT(DISTINCT {quoted_name}) AS unique_count,
                    MIN({quoted_name}) AS min_value,
                    MAX({quoted_name}) AS max_value,
                    {mean_expression}
                FROM "{schema.name}"
            """

            result = await self.runtime.query(
                sql,
                limit=1,
            )

            row = (
                result.rows[0]
                if result.rows
                else {}
            )

            total = row.get(
                "total_count",
                schema.row_count or 0,
            )

            non_null = row.get(
                "non_null_count",
                0,
            )

            null_count = total - non_null

            null_percentage = (
                null_count / total * 100
                if total
                else 0
            )

            profiles.append(
                ColumnProfile(
                    name=name,
                    dtype=column.dtype,
                    null_count=null_count,
                    null_percentage=null_percentage,
                    unique_count=row.get(
                        "unique_count"
                    ),
                    min_value=row.get(
                        "min_value"
                    ),
                    max_value=row.get(
                        "max_value"
                    ),
                    mean=self._safe_float(
                        row.get("mean_value")
                    ),
                )
            )

        return DatasetProfile(
            dataset_name=schema.name,
            row_count=schema.row_count or 0,
            column_count=len(schema.columns),
            columns=profiles,
        )

    @staticmethod
    def _safe_float(
        value: Any,
    ) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None
