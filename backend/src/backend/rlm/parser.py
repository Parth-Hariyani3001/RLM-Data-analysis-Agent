from __future__ import annotations

import re
from typing import Literal


class ResponseParser:
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

    def parse(
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
