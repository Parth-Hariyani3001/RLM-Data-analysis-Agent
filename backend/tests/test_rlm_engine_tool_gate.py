from __future__ import annotations

from typing import Any

import pytest

from backend.rlm.engine import RLMEngine
from backend.rlm.models import LLMMessage, LLMResponse, RLMConfig, StepType
from backend.rlm.provider import LLMProvider


class _ScriptedProvider(LLMProvider):
    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.calls = 0

    async def generate(self, messages: list[LLMMessage]) -> LLMResponse:
        if self.calls >= len(self.responses):
            raise AssertionError(
                f"Unexpected LLM call #{self.calls + 1}; "
                f"only {len(self.responses)} responses scripted."
            )
        content = self.responses[self.calls]
        self.calls += 1
        return LLMResponse(content=content, usage={})


class _MockRegistry:
    def __init__(self) -> None:
        self.collector = None

    def bind_collector(self, collector: Any) -> None:
        self.collector = collector

    async def sort_rows(
        self,
        column: str,
        ascending: bool = True,
        limit: int = 10,
    ) -> list[dict[str, object]]:
        if self.collector is not None:
            self.collector.record_tool_call("sort_rows")
        return [{"Name": "Item A", column: 59.99}]

    async def get_columns(self) -> list[dict[str, str]]:
        if self.collector is not None:
            self.collector.record_tool_call("get_columns")
        return [
            {"name": "Name", "dtype": "object"},
            {"name": "Price", "dtype": "float64"},
        ]

    def namespace(self) -> dict[str, Any]:
        return {
            "sort_rows": self.sort_rows,
            "get_columns": self.get_columns,
        }


@pytest.mark.asyncio
async def test_rejects_final_without_tools_then_succeeds_after_tool_use() -> None:
    provider = _ScriptedProvider(
        [
            "The top games are Zelda and Mario.",
            "<code>\nprint(await sort_rows('Price', ascending=False, limit=10))\n</code>",
            "<final>\n**Top row:** Item A — **$59.99**\n</final>",
        ]
    )
    engine = RLMEngine(
        provider=provider,
        tool_registry=_MockRegistry(),  # type: ignore[arg-type]
        config=RLMConfig(max_iterations=5),
    )

    result = await engine.run(question="Top 10 games priced descending")

    assert provider.calls == 3
    assert result.usage.tool_calls == 1
    assert "Item A" in result.answer
    error_steps = [step for step in result.steps if step.type == StepType.ERROR]
    assert len(error_steps) == 0


@pytest.mark.asyncio
async def test_max_iteration_without_tools_returns_failure_message() -> None:
    hallucinated = "<final>\nZelda costs $59.99\n</final>"
    provider = _ScriptedProvider([hallucinated] * 3)
    engine = RLMEngine(
        provider=provider,
        tool_registry=_MockRegistry(),  # type: ignore[arg-type]
        config=RLMConfig(max_iterations=3),
    )

    result = await engine.run(question="Top 10 games priced descending")

    assert result.answer == engine.NO_TOOLS_FAILURE_MESSAGE
    assert "Zelda" not in result.answer
    assert result.usage.tool_calls == 0
    assert result.iterations == 3


@pytest.mark.asyncio
async def test_strict_correction_after_repeated_no_tool_finals() -> None:
    provider = _ScriptedProvider(
        [
            "Here are the top games.",
            "<final>\nStill guessing.\n</final>",
            "<code>\nprint(await get_columns())\n</code>",
            "<final>\nDone.\n</final>",
        ]
    )
    engine = RLMEngine(
        provider=provider,
        tool_registry=_MockRegistry(),  # type: ignore[arg-type]
        config=RLMConfig(max_iterations=6),
    )

    result = await engine.run(question="Top 10 games priced descending")

    assert result.answer == "Done."
    assert result.usage.tool_calls == 1
    assert provider.calls == 4
    assert not any(step.type == StepType.ERROR for step in result.steps)


@pytest.mark.asyncio
async def test_final_allowed_after_tool_use() -> None:
    provider = _ScriptedProvider(
        [
            "<code>\nprint(await get_columns())\n</code>",
            "<final>\nColumns loaded.\n</final>",
        ]
    )
    engine = RLMEngine(
        provider=provider,
        tool_registry=_MockRegistry(),  # type: ignore[arg-type]
        config=RLMConfig(max_iterations=5),
    )

    result = await engine.run(question="What columns exist?")

    assert result.answer == "Columns loaded."
    assert result.usage.tool_calls == 1
    assert provider.calls == 2
