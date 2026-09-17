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

    # Accept ```python, ```py, bare ```, and other language tags.
    MARKDOWN_CODE_PATTERN = re.compile(
        r"```(?:[\w+-]*)?\s*\n?(.*?)\n?```",
        re.DOTALL | re.IGNORECASE,
    )

    TOOL_CALL_PATTERN = re.compile(
        r"await\s+(?:"
        r"profile_dataset|get_columns|count|sample|"
        r"value_counts|describe_column|describe|"
        r"filter_rows|sort_rows|analyze|quality_report|"
        r"correlation|percentiles|aggregate|"
        r"timeseries|detect_anomalies"
        r")\s*\(",
        re.IGNORECASE,
    )

    # Lines that look like executable Python (assignments, awaits, prints).
    PYTHONISH_LINE = re.compile(
        r"^\s*(?:"
        r"await\s+\w+\s*\(|"
        r"(?:print|len|min|max|sum|sorted|round|abs)\s*\(|"
        r"[A-Za-z_]\w*\s*=\s*.+"
        r")",
        re.MULTILINE,
    )

    RAW_OUTPUT_LIMIT = 800

    NO_TOOLS_FAILURE_MESSAGE = (
        "I could not query the dataset in time. "
        "Please try your question again."
    )

    NO_TOOLS_CORRECTION = (
        "You must inspect or query the dataset before answering. "
        "Return <code>...</code> with a tool call such as "
        "print(await get_columns()) or "
        'print(await sort_rows("Price", ascending=False, limit=10)). '
        "Do not answer from general knowledge. "
        "Do not return <final> until you have executed at least one tool."
    )

    NO_TOOLS_CORRECTION_STRICT = (
        "Your response must be <code> only — do not return <final> yet. "
        "Start with exactly:\n\n"
        "<code>\n"
        "print(await get_columns())\n"
        "</code>"
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
        consecutive_format_failures = 0
        consecutive_no_tool_finals = 0

        for iteration in range(
            1,
            self.config.max_iterations + 1,
        ):

            context.iteration = iteration
            self.collector.current_iteration = iteration

            if iteration == self.config.max_iterations:
                if self.collector.tool_calls == 0:
                    messages.append(
                        LLMMessage(
                            role="user",
                            content=(
                                "This is your final iteration and "
                                "you have not queried the dataset yet. "
                                "Return <final>...</final> explaining "
                                "that you could not retrieve data from "
                                "the dataset."
                            ),
                        )
                    )
                else:
                    messages.append(
                        LLMMessage(
                            role="user",
                            content=(
                                "This is your final iteration. "
                                "Do not execute more tools. "
                                "Return your best answer now using "
                                "<final>...</final> only, based on "
                                "evidence already gathered. If you "
                                "lack evidence, say what is missing."
                            ),
                        )
                    )

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
                consecutive_format_failures += 1
                truncated = content[: self.RAW_OUTPUT_LIMIT]
                if len(content) > self.RAW_OUTPUT_LIMIT:
                    truncated += "\n...[truncated]"

                error = (
                    "The model did not return <code> "
                    "or <final>."
                )
                if truncated:
                    error = f"{error}\n\nRaw model output:\n{truncated}"
                else:
                    error = f"{error}\n\nRaw model output: (empty)"

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

                if consecutive_format_failures >= 2:
                    correction = (
                        "Invalid response format again. "
                        "Reply with EXACTLY one of these shapes "
                        "and nothing else:\n\n"
                        "<code>\n"
                        "print(await get_columns())\n"
                        "</code>\n\n"
                        "or\n\n"
                        "<final>\n"
                        "**Your answer** formatted as Markdown\n"
                        "</final>\n\n"
                        "Do not use markdown code fences for REPL. "
                        "Do not write imports. Tools are already "
                        "available via await. Format final answers "
                        "as Markdown inside <final> tags."
                    )
                else:
                    correction = (
                        "Invalid response format. "
                        "Return either <code>...</code> "
                        "or <final>...</final>. "
                        "Do not use markdown code fences for REPL. "
                        "Format final answers as Markdown inside "
                        "<final> tags."
                    )

                messages.append(
                    LLMMessage(
                        role="user",
                        content=correction,
                    )
                )

                continue

            consecutive_format_failures = 0
            response_type, payload = parsed

            if response_type == "final" and self.collector.tool_calls == 0:
                if iteration == self.config.max_iterations:
                    answer = self.NO_TOOLS_FAILURE_MESSAGE
                    step = RLMStep(
                        type=StepType.FINAL,
                        content=answer,
                        iteration=iteration,
                    )
                    context.add_step(step)
                    if on_step:
                        await on_step(step)
                    usage = self.collector.to_usage()
                    usage.iterations = iteration
                    return RLMResult(
                        answer=answer,
                        iterations=iteration,
                        steps=context.steps,
                        usage=usage,
                    )

                consecutive_no_tool_finals += 1
                messages.append(
                    LLMMessage(
                        role="assistant",
                        content=content,
                    )
                )
                correction = (
                    self.NO_TOOLS_CORRECTION_STRICT
                    if consecutive_no_tool_finals >= 2
                    else self.NO_TOOLS_CORRECTION
                )
                messages.append(
                    LLMMessage(
                        role="user",
                        content=correction,
                    )
                )
                continue

            consecutive_no_tool_finals = 0

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
                        "using <final> tags, formatted as "
                        "Markdown (not markdown code fences)."
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

    def _extract_pythonish_block(self, content: str) -> str | None:
        """
        Pull likely-executable Python out of untagged model output.

        Prefer contiguous pythonish lines; fall back to a single
        tool-call line if present.
        """
        lines = content.splitlines()
        blocks: list[list[str]] = []
        current: list[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current:
                    current.append(line)
                continue

            if self.PYTHONISH_LINE.match(line) or self.TOOL_CALL_PATTERN.search(
                line
            ):
                current.append(line)
            else:
                if current:
                    blocks.append(current)
                    current = []

        if current:
            blocks.append(current)

        if blocks:
            # Prefer the longest contiguous pythonish block.
            best = max(blocks, key=lambda b: len("\n".join(b).strip()))
            extracted = "\n".join(best).strip()
            if extracted:
                return extracted

        tool_match = self.TOOL_CALL_PATTERN.search(content)
        if tool_match:
            # Expand to the full line containing the tool call.
            start = content.rfind("\n", 0, tool_match.start()) + 1
            end = content.find("\n", tool_match.end())
            if end == -1:
                end = len(content)
            return content[start:end].strip()

        return None

    def _looks_like_code(self, content: str) -> bool:
        if self.TOOL_CALL_PATTERN.search(content):
            return True
        if re.search(r"(?m)^\s*import\s+\w+", content):
            return True
        if re.search(r"(?m)^\s*from\s+\w+\s+import\s+", content):
            return True
        return bool(self.PYTHONISH_LINE.search(content))

    def _parse_response(
        self,
        content: str,
    ) -> tuple[Literal["final", "code"], str] | None:
        if not content or not content.strip():
            return None

        content = content.strip()

        final_match = self.FINAL_PATTERN.search(content)
        if final_match:
            return "final", final_match.group(1).strip()

        code_match = self.CODE_PATTERN.search(content)
        if code_match:
            return "code", code_match.group(1).strip()

        markdown_match = self.MARKDOWN_CODE_PATTERN.search(content)
        if markdown_match:
            code = markdown_match.group(1).strip()
            if code:
                return "code", code

        if self._looks_like_code(content):
            extracted = self._extract_pythonish_block(content)
            if extracted:
                return "code", extracted
            # Entire body may still be runnable (e.g. single await expr).
            return "code", content

        return "final", content
