from pathlib import Path

import polars as pl


def inspect_excel(path: str) -> dict:
    file_path = Path(path)

    df = pl.read_excel(
        file_path,
    )

    schema = {
        column: str(dtype)
        for column, dtype in df.schema.items()
    }

    return {
        "row_count": df.height,
        "column_count": len(df.columns),
        "schema": schema,
    }
