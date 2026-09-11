# app/data_runtime/factory.py

from __future__ import annotations

from pathlib import Path

from .exceptions import UnsupportedFileTypeError
from .runtime import DataRuntime
from .sources.csv import CSVSource
from .sources.excel import ExcelSource
from .sources.database import DatabaseSource


def create_file_runtime(
    path: str,
    table_name: str = "data",
) -> DataRuntime:
    extension = Path(path).suffix.lower()
    if extension == ".csv":
        source = CSVSource(
            path=path,
            table_name=table_name,
        )

    elif extension in {
        ".xlsx",
        ".xls",
    }:
        source = ExcelSource(
            path=path,
            table_name=table_name,
        )

    else:
        raise UnsupportedFileTypeError(
            f"Unsupported file type: {extension}"
        )

    return DataRuntime(source)


def create_database_runtime(
    connection_url: str,
    table_name: str,
) -> DataRuntime:

    source = DatabaseSource(
        connection_url=connection_url,
        table_name=table_name,
    )

    return DataRuntime(source)
