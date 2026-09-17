from pathlib import Path

import polars as pl

from backend.data_runtime.csv_encoding import (
    detect_csv_encoding,
    polars_csv_kwargs,
    supports_polars_lazy_scan,
)


def inspect_csv(path: str) -> dict:
    file_path = Path(path)
    encoding = detect_csv_encoding(file_path)
    read_kwargs = polars_csv_kwargs(encoding)

    df = pl.read_csv(
        file_path,
        n_rows=1000,
        **read_kwargs,
    )

    if supports_polars_lazy_scan(encoding):
        row_count = (
            pl.scan_csv(
                file_path, **polars_csv_kwargs(encoding, for_lazy=True))
            .select(pl.len())
            .collect()
            .item()
        )
    else:
        row_count = pl.read_csv(file_path, **read_kwargs).height

    schema = {
        column: str(dtype)
        for column, dtype in df.schema.items()
    }

    return {
        "row_count": row_count,
        "column_count": len(df.columns),
        "schema": schema,
    }
