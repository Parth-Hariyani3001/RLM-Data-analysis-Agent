from __future__ import annotations

import ast
import asyncio
import io
from contextlib import redirect_stdout
from typing import Any


class REPLSecurityError(Exception):
    pass


class RLMRepl:
    """
    Restricted Python execution environment for the RLM.

    The model receives:
        - analytical tools
        - basic Python utilities
        - variables created during previous iterations

    It does NOT receive:
        - filesystem access
        - os
        - subprocess
        - socket
        - arbitrary imports
        - application globals
    """

    ALLOWED_BUILTINS = {
        "len": len,
        "min": min,
        "max": max,
        "sum": sum,
        "sorted": sorted,
        "round": round,
        "abs": abs,
        "enumerate": enumerate,
        "range": range,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "isinstance": isinstance,
        "print": print,
    }

    BLOCKED_NODES = (
        ast.Import,
        ast.ImportFrom,
    )

    BLOCKED_NAMES = {
        "open",
        "exec",
        "eval",
        "compile",
        "__import__",
        "globals",
        "locals",
        "vars",
        "input",
        "breakpoint",
    }

    def __init__(
        self,
        namespace: dict[str, Any] | None = None,
        max_output: int = 20_000,
    ):
        self.namespace = namespace or {}
        self.max_output = max_output

        self.namespace["__builtins__"] = self.ALLOWED_BUILTINS

    def validate(self, code: str) -> None:
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            raise REPLSecurityError(
                f"Invalid Python: {exc}"
            ) from exc

        for node in ast.walk(tree):
            if isinstance(node, self.BLOCKED_NODES):
                raise REPLSecurityError(
                    "Imports are not allowed in the RLM REPL."
                )

            if isinstance(node, ast.Name):
                if node.id in self.BLOCKED_NAMES:
                    raise REPLSecurityError(
                        f"Use of '{node.id}' is not allowed."
                    )

            if isinstance(node, ast.Attribute):
                if node.attr.startswith("__"):
                    raise REPLSecurityError(
                        "Dunder attributes are not allowed."
                    )

    async def execute(self, code: str) -> str:
        self.validate(code)

        stdout = io.StringIO()

        try:
            with redirect_stdout(stdout):
                result = await self._exec_async(code)

        except Exception as exc:
            return f"REPL_ERROR: {type(exc).__name__}: {exc}"

        output = stdout.getvalue()

        if result is not None:
            if output:
                output += "\n"

            output += repr(result)

        if len(output) > self.max_output:
            output = (
                output[: self.max_output]
                + "\n...[output truncated]"
            )

        return output

    async def _exec_async(self, code: str) -> Any:
        """
        Execute code while supporting:
            await tool()
        and normal Python statements.

        We transform top-level statements into an async function.
        """

        tree = ast.parse(code, mode="exec")
        body = tree.body
        if not body:
            return None

        # If the final statement is an expression,
        # preserve its result.
        last = body[-1]

        if isinstance(last, ast.Expr):
            body[-1] = ast.Return(value=last.value)

        function = ast.AsyncFunctionDef(
            name="_rlm_exec",
            args=ast.arguments(
                posonlyargs=[],
                args=[],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
                vararg=None,
                kwarg=None,
            ),
            body=body,
            decorator_list=[],
            returns=None,
            type_comment=None,
        )

        module = ast.Module(
            body=[function],
            type_ignores=[],
        )

        ast.fix_missing_locations(module)
        namespace = dict(self.namespace)

        exec(
            compile(
                module,
                filename="<rlm>",
                mode="exec",
            ),
            namespace,
        )

        result = await namespace["_rlm_exec"]()

        # Persist variables created by the model.
        for key, value in namespace.items():
            if not key.startswith("_"):
                self.namespace[key] = value

        return result
