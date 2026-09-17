from __future__ import annotations

from typing import Awaitable, Callable

from .corrections import (
    NO_TOOLS_FAILURE_MESSAGE,
    format_correction,
    format_error_message,
    last_iteration_nudge,
    no_tool_correction,
    repl_result_followup,
)
from .context import RLMContext
from .models import (
    LLMMessage,
    RLMConfig,
    RLMResult,
    RLMStep,
    RunCollector,
    StepType,
)
from .parser import ResponseParser
from .prompts import (
    build_initial_prompt,
    build_system_prompt,
)
from .provider import LLMProvider
from .repl import RLMRepl
from .session import RunSession
from .tools import ToolRegistry


class RLMEngine:
    NO_TOOLS_FAILURE_MESSAGE = NO_TOOLS_FAILURE_MESSAGE

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
        self.parser = ResponseParser()

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
        session = RunSession(
            context=RLMContext(question=question),
            repl=RLMRepl(
                namespace=self.tool_registry.namespace(),
                max_output=self.config.max_repl_output,
            ),
            messages=[
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
            ],
            collector=self.collector,
            config=self.config,
        )

        model = getattr(self.provider, "model", None)

        for iteration in range(1, self.config.max_iterations + 1):
            session.begin_iteration(iteration)

            if iteration == self.config.max_iterations:
                session.append_user(
                    last_iteration_nudge(session.collector.tool_calls > 0)
                )

            response = await self.provider.generate(session.messages)
            self.collector.record_llm_call(response.usage, model=model)

            result = await self._handle_response(
                session=session,
                content=response.content.strip(),
                iteration=iteration,
                on_step=on_step,
            )
            if result is not None:
                return result

        raise RuntimeError(
            f"RLM reached maximum iterations "
            f"({self.config.max_iterations}) "
            "without producing a final answer."
        )

    async def _handle_response(
        self,
        session: RunSession,
        content: str,
        iteration: int,
        on_step: Callable[[RLMStep], Awaitable[None]] | None,
    ) -> RLMResult | None:
        parsed = self.parser.parse(content)

        if parsed is None:
            return await self._handle_parse_failure(
                session=session,
                content=content,
                iteration=iteration,
                on_step=on_step,
            )

        session.consecutive_format_failures = 0
        response_type, payload = parsed

        if response_type == "final" and session.collector.tool_calls == 0:
            return await self._handle_premature_final(
                session=session,
                content=content,
                iteration=iteration,
                on_step=on_step,
            )

        session.consecutive_no_tool_finals = 0

        if response_type == "final":
            return await self._handle_final(
                session=session,
                payload=payload,
                iteration=iteration,
                on_step=on_step,
            )

        return await self._handle_code(
            session=session,
            content=content,
            code=payload,
            iteration=iteration,
            on_step=on_step,
        )

    async def _handle_parse_failure(
        self,
        session: RunSession,
        content: str,
        iteration: int,
        on_step: Callable[[RLMStep], Awaitable[None]] | None,
    ) -> None:
        session.consecutive_format_failures += 1
        error = format_error_message(content)

        step = RLMStep(
            type=StepType.ERROR,
            content=error,
            iteration=iteration,
        )

        session.context.add_step(step)
        session.collector.record_error(error)

        if on_step:
            await on_step(step)

        session.append_assistant(content)
        session.append_user(
            format_correction(session.consecutive_format_failures)
        )

    async def _handle_premature_final(
        self,
        session: RunSession,
        content: str,
        iteration: int,
        on_step: Callable[[RLMStep], Awaitable[None]] | None,
    ) -> RLMResult | None:
        if iteration == self.config.max_iterations:
            answer = NO_TOOLS_FAILURE_MESSAGE
            step = RLMStep(
                type=StepType.FINAL,
                content=answer,
                iteration=iteration,
            )
            session.context.add_step(step)
            if on_step:
                await on_step(step)
            usage = session.collector.to_usage()
            usage.iterations = iteration
            return RLMResult(
                answer=answer,
                iterations=iteration,
                steps=session.context.steps,
                usage=usage,
            )

        session.consecutive_no_tool_finals += 1
        session.append_assistant(content)
        session.append_user(
            no_tool_correction(session.consecutive_no_tool_finals)
        )
        return None

    async def _handle_final(
        self,
        session: RunSession,
        payload: str,
        iteration: int,
        on_step: Callable[[RLMStep], Awaitable[None]] | None,
    ) -> RLMResult:
        step = RLMStep(
            type=StepType.FINAL,
            content=payload,
            iteration=iteration,
        )

        session.context.add_step(step)

        if on_step:
            await on_step(step)

        usage = session.collector.to_usage()
        usage.iterations = iteration

        return RLMResult(
            answer=payload,
            iterations=iteration,
            steps=session.context.steps,
            usage=usage,
        )

    async def _handle_code(
        self,
        session: RunSession,
        content: str,
        code: str,
        iteration: int,
        on_step: Callable[[RLMStep], Awaitable[None]] | None,
    ) -> None:
        code_step = RLMStep(
            type=StepType.CODE,
            content=code,
            iteration=iteration,
        )

        session.context.add_step(code_step)
        session.collector.record_code()

        if on_step:
            await on_step(code_step)

        result = await session.repl.execute(code)

        result_step = RLMStep(
            type=StepType.RESULT,
            content=result,
            iteration=iteration,
        )

        session.context.add_step(result_step)
        session.context.observe(result)

        if on_step:
            await on_step(result_step)

        session.append_assistant(content)
        session.append_user(repl_result_followup(result))
        session.trim_messages()
