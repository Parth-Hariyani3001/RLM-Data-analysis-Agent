from __future__ import annotations

import pandas as pd

from .models import Anomaly, AnomalyResult


class AnomalyDetector:

    # --------------------------------------------------------
    # Z-SCORE
    # --------------------------------------------------------

    @staticmethod
    def zscore(
        df: pd.DataFrame,
        column: str,
        threshold: float = 3.0,
    ) -> AnomalyResult:

        if column not in df.columns:
            raise ValueError(f"Unknown column: {column}")

        values = pd.to_numeric(df[column], errors="coerce")
        mean = values.mean()
        std = values.std()

        if pd.isna(std) or std == 0:
            return AnomalyResult(
                column=column,
                method="zscore",
                threshold=threshold,
                anomalies=[],
                total_anomalies=0,
            )

        scores = (values - mean) / std
        anomalies = []

        for row_index, (score, value) in enumerate(zip(scores, values)):
            if pd.isna(score):
                continue
            if abs(float(score)) >= threshold:
                anomalies.append(Anomaly(
                    row_index=row_index,
                    value=float(value),
                    score=float(score),
                    method="zscore",
                ))

        return AnomalyResult(
            column=column,
            method="zscore",
            threshold=threshold,
            anomalies=anomalies,
            total_anomalies=len(anomalies),
        )

    # --------------------------------------------------------
    # IQR
    # --------------------------------------------------------

    @staticmethod
    def iqr(
        df: pd.DataFrame,
        column: str,
        multiplier: float = 1.5,
    ) -> AnomalyResult:

        if column not in df.columns:
            raise ValueError(f"Unknown column: {column}")

        values = pd.to_numeric(df[column], errors="coerce")
        valid = values.dropna()

        if valid.empty:
            return AnomalyResult(
                column=column,
                method="iqr",
                threshold=multiplier,
                anomalies=[],
                total_anomalies=0,
            )

        q1 = float(valid.quantile(0.25))
        q3 = float(valid.quantile(0.75))
        iqr = q3 - q1
        lower = q1 - multiplier * iqr
        upper = q3 + multiplier * iqr
        anomalies = []

        for row_index, value in enumerate(values):
            if pd.isna(value):
                continue
            v = float(value)
            if v < lower or v > upper:
                score = (lower - v) / iqr if v < lower else (v - upper) / iqr
                if not iqr:
                    score = 0.0
                anomalies.append(Anomaly(
                    row_index=row_index,
                    value=v,
                    score=float(score),
                    method="iqr",
                ))

        return AnomalyResult(
            column=column,
            method="iqr",
            threshold=multiplier,
            anomalies=anomalies,
            total_anomalies=len(anomalies),
        )
