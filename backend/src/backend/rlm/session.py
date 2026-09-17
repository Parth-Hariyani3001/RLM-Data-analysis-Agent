from __future__ import annotations

from dataclasses import dataclass, field

from .context import RLMContext
from .models import LLMMessage, RLMConfig, RunCollector
from .repl import RLMRepl


@dataclass
class RunSession:
    context: RLMContext
    repl: RLMRepl
    messages: list[LLMMessage]
    collector: RunCollector
    config: RLMConfig
    consecutive_format_failures: int = 0
    consecutive_no_tool_finals: int = 0
    iteration: int = field(default=0, init=False)

    def begin_iteration(self, iteration: int) -> None:
        self.iteration = iteration
        self.context.iteration = iteration
        self.collector.current_iteration = iteration

    def append_assistant(self, content: str) -> None:
        self.messages.append(
            LLMMessage(
                role="assistant",
                content=content,
            )
        )

    def append_user(self, content: str) -> None:
        self.messages.append(
            LLMMessage(
                role="user",
                content=content,
            )
        )

    def trim_messages(self) -> None:
        total_length = sum(
            len(message.content)
            for message in self.messages
        )

        if total_length <= self.config.max_context_length:
            return

        # Always preserve system message.
        system = self.messages[0]
        recent = self.messages[1:]

        while (
            recent
            and sum(len(message.content) for message in recent)
            > self.config.max_context_length
        ):
            recent.pop(0)

        self.messages = [system, *recent]
