from __future__ import annotations

import pytest

from backend.rlm.parser import ResponseParser


@pytest.fixture
def parser() -> ResponseParser:
    return ResponseParser()


@pytest.mark.parametrize(
    ("content", "expected_type", "expected_payload"),
    [
        (
            "<final>\nThe answer is 42.\n</final>",
            "final",
            "The answer is 42.",
        ),
        (
            "<code>\nprint(await get_columns())\n</code>",
            "code",
            "print(await get_columns())",
        ),
        (
            "```python\nprint(await count())\n```",
            "code",
            "print(await count())",
        ),
        (
            "```\nprint(await sample(5))\n```",
            "code",
            "print(await sample(5))",
        ),
        (
            "await get_columns()",
            "code",
            "await get_columns()",
        ),
        (
            "await sort_rows(\"Price\", ascending=False, limit=10)",
            "code",
            "await sort_rows(\"Price\", ascending=False, limit=10)",
        ),
        (
            "Let me inspect the schema first.\n"
            "await get_columns()\n"
            "Then we can continue.",
            "code",
            "await get_columns()",
        ),
        (
            "cols = await get_columns()\nprint(cols)",
            "code",
            "cols = await get_columns()\nprint(cols)",
        ),
        (
            "The most expensive game is Portal at $9.99.",
            "final",
            "The most expensive game is Portal at $9.99.",
        ),
        (
            "",
            None,
            None,
        ),
        (
            "   ",
            None,
            None,
        ),
    ],
)
def test_parse_response(
    parser: ResponseParser,
    content: str,
    expected_type: str | None,
    expected_payload: str | None,
) -> None:
    parsed = parser.parse(content)

    if expected_type is None:
        assert parsed is None
        return

    assert parsed is not None
    response_type, payload = parsed
    assert response_type == expected_type
    assert payload == expected_payload


def test_parse_response_prefers_final_over_code(parser: ResponseParser) -> None:
    content = (
        "<code>\nprint(1)\n</code>\n"
        "<final>\nDone\n</final>"
    )
    parsed = parser.parse(content)
    assert parsed == ("final", "Done")


def test_parse_response_import_prose_recovers_tool_call(
    parser: ResponseParser,
) -> None:
    """Prose mentioning import plus a tool call should recover as code."""
    content = (
        "I will not import pandas. Instead:\n"
        "print(await describe())\n"
    )
    parsed = parser.parse(content)
    assert parsed is not None
    assert parsed[0] == "code"
    assert "await describe()" in parsed[1]


def test_parse_response_raw_import_treated_as_code(parser: ResponseParser) -> None:
    content = "import pandas as pd\ndf.head()"
    parsed = parser.parse(content)
    assert parsed is not None
    assert parsed[0] == "code"


def test_parse_response_prose_with_await_word_is_final(parser: ResponseParser) -> None:
    """Natural-language 'await' must not force a code path."""
    content = "I will await further clarification before answering."
    parsed = parser.parse(content)
    assert parsed == (
        "final",
        "I will await further clarification before answering.",
    )
