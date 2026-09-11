from __future__ import annotations

import re
from typing import Awaitable, Callable, Literal

from .context import RLMContext
from .models import (
    LLMMessage,
    RLMConfig,
    RLMResult,
    RLMStep,
    RunCollector,
    StepType,
)
from .prompts import (
    build_initial_prompt,
    build_system_prompt,
)
from .provider import LLMProvider
from .repl import RLMRepl
from .tools import ToolRegistry


class RLMEngine:
    CODE_PATTERN = re.compile(
        r"<code>\s*(.*?)\s*</code>",
        re.DOTALL | re.IGNORECASE,
    )

    FINAL_PATTERN = re.compile(
        r"<final>\s*(.*?)\s*</final>",
        re.DOTALL | re.IGNORECASE,
    )

    MARKDOWN_CODE_PATTERN = re.compile(
        r"```(?:python)?\s*(.*?)\s*```",
        re.DOTALL | re.IGNORECASE,
    )

    def __init__(
        self,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
        config: RLMConfig | None = None,
        collector: RunCollector | None = None,
    ):
        self.provider = provider
        self.tool_registry = tool_registry
        self.config = config or RLMConfig()
        self.collector = collector or RunCollector()
        self.tool_registry.bind_collector(self.collector)

    async def run(
        self,
        question: str,
        on_step: Callable[
            [RLMStep],
            Awaitable[None],
        ]
        | None = None,
        dataset_context: str | None = None,
    ) -> RLMResult:

        context = RLMContext(
            question=question,
        )

        repl = RLMRepl(
            namespace=self.tool_registry.namespace(),
            max_output=self.config.max_repl_output,
        )

        messages = [
            LLMMessage(
                role="system",
                content=build_system_prompt(),
            ),
            LLMMessage(
                role="user",
                content=build_initial_prompt(
                    question,
                    dataset_context=dataset_context,
                ),
            ),
        ]

        model = getattr(self.provider, "model", None)

        for iteration in range(
            1,
            self.config.max_iterations + 1,
        ):

            context.iteration = iteration
            self.collector.current_iteration = iteration

            response = await self.provider.generate(
                messages
            )
            self.collector.record_llm_call(
                response.usage,
                model=model,
            )

            content = response.content.strip()
            parsed = self._parse_response(content)

            if parsed is None:
                error = (
                    "The model did not return <code> "
                    "or <final>."
                )

                step = RLMStep(
                    type=StepType.ERROR,
                    content=error,
                    iteration=iteration,
                )

                context.add_step(step)
                self.collector.record_error(error)

                if on_step:
                    await on_step(step)

                messages.append(
                    LLMMessage(
                        role="assistant",
                        content=content,
                    )
                )

                messages.append(
                    LLMMessage(
                        role="user",
                        content=(
                            "Invalid response format. "
                            "Return either <code>...</code> "
                            "or <final>...</final>. "
                            "Do not use markdown code fences."
                        ),
                    )
                )

                continue

            response_type, payload = parsed

            if response_type == "final":
                step = RLMStep(
                    type=StepType.FINAL,
                    content=payload,
                    iteration=iteration,
                )

                context.add_step(step)

                if on_step:
                    await on_step(step)

                usage = self.collector.to_usage()
                usage.iterations = iteration

                return RLMResult(
                    answer=payload,
                    iterations=iteration,
                    steps=context.steps,
                    usage=usage,
                )

            code = payload

            code_step = RLMStep(
                type=StepType.CODE,
                content=code,
                iteration=iteration,
            )

            context.add_step(code_step)
            self.collector.record_code()

            if on_step:
                await on_step(code_step)

            # -----------------------------------------
            # EXECUTE CODE
            # -----------------------------------------

            result = await repl.execute(code)

            result_step = RLMStep(
                type=StepType.RESULT,
                content=result,
                iteration=iteration,
            )

            context.add_step(result_step)

            context.observe(result)

            if on_step:
                await on_step(result_step)

            # -----------------------------------------
            # CONTINUE RECURSION
            # -----------------------------------------

            messages.append(
                LLMMessage(
                    role="assistant",
                    content=content,
                )
            )

            messages.append(
                LLMMessage(
                    role="user",
                    content=(
                        "REPL execution result:\n\n"
                        f"{result}\n\n"
                        "Use this result to continue "
                        "your analysis. If more analysis "
                        "is needed, execute another "
                        "piece of Python inside <code> tags. "
                        "Otherwise return the final answer "
                        "using <final> tags only (not markdown "
                        "fences or plain prose)."
                    ),
                )
            )

            # Keep context from growing indefinitely.
            messages = self._trim_messages(messages)

        raise RuntimeError(
            f"RLM reached maximum iterations "
            f"({self.config.max_iterations}) "
            "without producing a final answer."
        )

    def _trim_messages(
        self,
        messages: list[LLMMessage],
    ) -> list[LLMMessage]:

        total_length = sum(
            len(message.content)
            for message in messages
        )

        if total_length <= self.config.max_context_length:
            return messages

        # Always preserve system message.
        system = messages[0]

        recent = messages[1:]

        while (
            recent
            and sum(len(m.content) for m in recent)
            > self.config.max_context_length
        ):
            recent.pop(0)

        return [system, *recent]

    def _parse_response(
        self,
        content: str,
    ) -> tuple[Literal["final", "code"], str] | None:
        final_match = self.FINAL_PATTERN.search(content)
        if final_match:
            return "final", final_match.group(1).strip()

        code_match = self.CODE_PATTERN.search(content)
        if code_match:
            return "code", code_match.group(1).strip()

        markdown_match = self.MARKDOWN_CODE_PATTERN.search(content)
        if markdown_match:
            return "code", markdown_match.group(1).strip()

        if content and "await " not in content and "import " not in content:
            return "final", content

        return None
