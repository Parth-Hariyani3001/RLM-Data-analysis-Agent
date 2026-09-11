from __future__ import annotations

from pathlib import Path

from charset_normalizer import from_path

_DEFAULT_ENCODING = "utf-8"

_POLARS_READ_ENCODING = {
    "utf-8": "utf8",
    "utf8": "utf8",
    "ascii": "utf8",
    "utf-8-sig": "utf8",
    "cp1252": "windows-1252",
    "windows-1252": "windows-1252",
    "latin-1": "latin-1",
    "iso-8859-1": "latin-1",
}


def detect_csv_encoding(path: str | Path) -> str:
    """Detect a CSV file encoding from file contents."""
    result = from_path(path).best()
    if result is None:
        return _DEFAULT_ENCODING

    encoding = result.encoding.lower().replace("_", "-")

    if encoding in {"utf-8", "utf8", "ascii"}:
        return "utf-8"

    if encoding in {"utf-8-sig", "utf8-sig"}:
        return "utf-8"

    return result.encoding


def to_duckdb_encoding(encoding: str) -> str:
    """Map a detected encoding to a DuckDB read_csv encoding name."""
    normalized = encoding.lower().replace("_", "-")

    if normalized in {"utf-8", "utf8", "ascii", "utf-8-sig", "utf8-sig"}:
        return "UTF-8"

    return encoding


def to_polars_read_encoding(encoding: str) -> str:
    """Map a detected encoding to a Polars read_csv encoding name."""
    normalized = encoding.lower().replace("_", "-")
    return _POLARS_READ_ENCODING.get(normalized, encoding)


def supports_polars_lazy_scan(encoding: str) -> bool:
    """Whether Polars scan_csv can read this encoding."""
    normalized = encoding.lower().replace("_", "-")
    return normalized in {"utf-8", "utf8", "ascii", "utf-8-sig", "utf8-sig"}


def polars_csv_kwargs(
    encoding: str,
    *,
    for_lazy: bool = False,
) -> dict[str, str | bool]:
    """Shared Polars CSV reader options for messy user uploads."""
    if for_lazy and supports_polars_lazy_scan(encoding):
        polars_encoding = "utf8"
    else:
        polars_encoding = to_polars_read_encoding(encoding)

    return {
        "encoding": polars_encoding,
        "truncate_ragged_lines": True,
    }


def duckdb_read_csv_options(path: str | Path) -> str:
    """DuckDB read_csv option string for messy user uploads."""
    encoding = to_duckdb_encoding(detect_csv_encoding(path))
    return (
        f"auto_detect=true, encoding='{encoding}', "
        "ignore_errors=true"
    )
