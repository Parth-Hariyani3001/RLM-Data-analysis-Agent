from __future__ import annotations

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

RAW_OUTPUT_LIMIT = 800


def format_error_message(raw_output: str, limit: int = RAW_OUTPUT_LIMIT) -> str:
    truncated = raw_output[:limit]
    if len(raw_output) > limit:
        truncated += "\n...[truncated]"

    error = "The model did not return <code> or <final>."
    if truncated:
        return f"{error}\n\nRaw model output:\n{truncated}"
    return f"{error}\n\nRaw model output: (empty)"


def format_correction(consecutive_format_failures: int) -> str:
    if consecutive_format_failures >= 2:
        return (
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

    return (
        "Invalid response format. "
        "Return either <code>...</code> "
        "or <final>...</final>. "
        "Do not use markdown code fences for REPL. "
        "Format final answers as Markdown inside "
        "<final> tags."
    )


def no_tool_correction(consecutive_no_tool_finals: int) -> str:
    if consecutive_no_tool_finals >= 2:
        return NO_TOOLS_CORRECTION_STRICT
    return NO_TOOLS_CORRECTION


def last_iteration_nudge(has_tools: bool) -> str:
    if not has_tools:
        return (
            "This is your final iteration and "
            "you have not queried the dataset yet. "
            "Return <final>...</final> explaining "
            "that you could not retrieve data from "
            "the dataset."
        )

    return (
        "This is your final iteration. "
        "Do not execute more tools. "
        "Return your best answer now using "
        "<final>...</final> only, based on "
        "evidence already gathered. If you "
        "lack evidence, say what is missing."
    )


def repl_result_followup(result: str) -> str:
    return (
        "REPL execution result:\n\n"
        f"{result}\n\n"
        "Use this result to continue "
        "your analysis. If more analysis "
        "is needed, execute another "
        "piece of Python inside <code> tags. "
        "Otherwise return the final answer "
        "using <final> tags, formatted as "
        "Markdown (not markdown code fences)."
    )
