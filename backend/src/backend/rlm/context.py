from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import RLMStep


@dataclass
class RLMContext:
    question: str
    variables: dict[str, Any] = field(default_factory=dict)
    observations: list[str] = field(default_factory=list)
    steps: list[RLMStep] = field(default_factory=list)
    iteration: int = 0

    def set(self, name: str, value: Any) -> None:
        self.variables[name] = value

    def get(self, name: str, default: Any = None) -> Any:
        return self.variables.get(name, default)

    def observe(self, observation: str) -> None:
        self.observations.append(observation)

    def add_step(self, step: RLMStep) -> None:
        self.steps.append(step)

    def snapshot(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "variables": self.variables,
            "observations": self.observations,
            "iteration": self.iteration,
        }