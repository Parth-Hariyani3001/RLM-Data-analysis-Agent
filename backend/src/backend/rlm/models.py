from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StepType(str, Enum):
    THINK = "think"
    CODE = "code"
    TOOL = "tool"
    RESULT = "result"
    FINAL = "final"
    ERROR = "error"


@dataclass
class RLMConfig:
    max_iterations: int = 15
    max_repl_output: int = 20_000
    max_context_length: int = 100_000


@dataclass
class RLMRequest:
    question: str
    dataset_id: str | None = None


@dataclass
class RunCollector:
    """Accumulates LLM/tool telemetry for a single agent turn."""

    model: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    llm_calls: int = 0
    tool_calls: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)
    current_iteration: int = 0

    def record_llm_call(self, usage: dict[str, Any], model: str | None = None) -> None:
        if model:
            self.model = model

        prompt = int(usage.get("prompt_tokens") or 0)
        completion = int(usage.get("completion_tokens") or 0)
        total = int(usage.get("total_tokens") or (prompt + completion))

        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens += total
        self.llm_calls += 1

        self.events.append(
            {
                "type": "llm_call",
                "iteration": self.current_iteration,
                "model": model or self.model,
                "prompt_tokens": prompt,
                "completion_tokens": completion,
                "total_tokens": total,
            }
        )

    def record_tool_call(self, name: str) -> None:
        self.tool_calls += 1
        self.events.append(
            {
                "type": "tool_call",
                "iteration": self.current_iteration,
                "name": name,
            }
        )

    def record_code(self) -> None:
        self.events.append(
            {
                "type": "code",
                "iteration": self.current_iteration,
            }
        )

    def record_error(self, content: str | None = None) -> None:
        event: dict[str, Any] = {
            "type": "error",
            "iteration": self.current_iteration,
        }
        if content:
            event["content"] = content
        self.events.append(event)

    def to_usage(self) -> RLMUsage:
        return RLMUsage(
            model=self.model,
            iterations=self.current_iteration,
            llm_calls=self.llm_calls,
            tool_calls=self.tool_calls,
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            total_tokens=self.total_tokens,
            events=list(self.events),
        )


@dataclass
class RLMUsage:
    model: str | None = None
    iterations: int = 0
    llm_calls: int = 0
    tool_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "iterations": self.iterations,
            "llm_calls": self.llm_calls,
            "tool_calls": self.tool_calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "events": self.events,
        }


@dataclass
class RLMResult:
    answer: str
    iterations: int
    steps: list[RLMStep] = field(default_factory=list)
    usage: RLMUsage = field(default_factory=RLMUsage)


@dataclass
class RLMStep:
    type: StepType
    content: str
    iteration: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMMessage:
    role: str
    content: str


@dataclass
class LLMResponse:
    content: str
    usage: dict[str, Any] = field(default_factory=dict)
