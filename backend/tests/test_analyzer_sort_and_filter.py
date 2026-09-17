from __future__ import annotations

import pandas as pd
import pytest

from backend.analysis.analyzer import Analyzer
from backend.rlm.tools import AnalysisTools


class _FakeRuntime:
    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df

    async def to_dataframe(self) -> pd.DataFrame:
        return self._df.copy()


def _analyzer() -> Analyzer:
    df = pd.DataFrame(
        {
            "Name": ["Cheap", "Mid", "Pricey"],
            "Price": [1.0, 5.0, 10.0],
            "Platform": ["PC", "PC", "Switch"],
        }
    )
    return Analyzer(_FakeRuntime(df))  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_sort_rows_highest_first() -> None:
    analyzer = _analyzer()
    rows = await analyzer.sort_rows("Price", ascending=False, limit=2)
    assert [row["Name"] for row in rows] == ["Pricey", "Mid"]
    assert rows[0]["Price"] == 10.0


@pytest.mark.asyncio
async def test_sort_rows_lowest_first() -> None:
    analyzer = _analyzer()
    rows = await analyzer.sort_rows("Price", ascending=True, limit=1)
    assert rows == [{"Name": "Cheap", "Price": 1.0, "Platform": "PC"}]


@pytest.mark.asyncio
async def test_sort_rows_unknown_column() -> None:
    analyzer = _analyzer()
    with pytest.raises(ValueError, match="Unknown column"):
        await analyzer.sort_rows("Missing")


@pytest.mark.asyncio
async def test_filter_rejects_sql_order_by() -> None:
    analyzer = _analyzer()
    with pytest.raises(ValueError, match="pandas query") as exc_info:
        await analyzer.filter("ORDER BY Price DESC LIMIT 10")
    message = str(exc_info.value)
    assert "sort_rows" in message
    assert "not SQL" in message


@pytest.mark.asyncio
async def test_filter_pandas_query_works() -> None:
    analyzer = _analyzer()
    rows = await analyzer.filter("Price > 5 and Platform == 'Switch'")
    assert [row["Name"] for row in rows] == ["Pricey"]


@pytest.mark.asyncio
async def test_filter_wraps_invalid_query() -> None:
    analyzer = _analyzer()
    with pytest.raises(ValueError, match="pandas query"):
        await analyzer.filter("this is not a valid query @@@")


@pytest.mark.asyncio
async def test_filter_rows_tool_rejects_sql() -> None:
    tools = AnalysisTools(_FakeRuntime(pd.DataFrame({"Price": [1, 2]})))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="sort_rows"):
        await tools.filter_rows("ORDER BY Price DESC LIMIT 10")
