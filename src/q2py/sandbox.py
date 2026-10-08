"""Execute generated Python without giving it the host builtins.

This is the local sandbox: an AST allow-list plus a short-lived subprocess with
a stripped environment, a CPU limit, an address-space limit, and a timeout.
It is not a container. Network and filesystem calls are unavailable to generated
code because the builtins exposed to it do not include them.
"""

from __future__ import annotations

import ast
import inspect
import json
import os
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from q2py.diagnostics import Diagnostic, error

_ALLOWED_NODES = {
    ast.Module,
    ast.Import,
    ast.alias,
    ast.FunctionDef,
    ast.arguments,
    ast.arg,
    ast.Return,
    ast.Assign,
    ast.Expr,
    ast.Name,
    ast.Load,
    ast.Store,
    ast.Call,
    ast.Attribute,
    ast.Constant,
    ast.List,
    ast.Tuple,
    ast.keyword,
    ast.Lambda,
    ast.Subscript,
    ast.BinOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.BitOr,
    ast.BitAnd,
    ast.Compare,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.Gt,
    ast.LtE,
    ast.GtE,
    ast.UnaryOp,
    ast.USub,
    ast.Not,
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.IfExp,
    ast.Dict,
    ast.FormattedValue,
    ast.JoinedStr,
    ast.Starred,
    ast.Slice,
}


class Executor(Protocol):
    def run(self, source: str) -> ExecResult: ...


@dataclass
class ExecResult:
    ok: bool
    canon: dict[str, object] | None
    display: str
    signal: str | None
    message: str
    diagnostics: list[Diagnostic]


def validate_generated(source: str) -> list[Diagnostic]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [error("compile", f"generated Python did not parse: {exc.msg}", exc.lineno or 1, exc.offset or 1, "Q2PY500")]
    problems: list[Diagnostic] = []
    for node in ast.walk(tree):
        if type(node) not in _ALLOWED_NODES:
            problems.append(
                error(
                    "compile",
                    f"sandbox rejected generated syntax {type(node).__name__}",
                    getattr(node, "lineno", 1),
                    getattr(node, "col_offset", 1),
                    "Q2PY501",
                )
            )
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
            if names != ["q2py.runtime"]:
                problems.append(error("compile", "sandbox rejected import", node.lineno, node.col_offset, "Q2PY502"))
        if isinstance(node, ast.Name) and node.id.startswith("_") and node.id != "_":
            # Generated locals are `_vN` and `_lamN`. Dunder names are not.
            if node.id.startswith("__"):
                problems.append(error("compile", f"sandbox rejected name {node.id}", node.lineno, node.col_offset, "Q2PY504"))
        if isinstance(node, ast.Attribute):
            reason = _attribute_reason(node)
            if reason:
                problems.append(error("compile", reason, node.lineno, node.col_offset, "Q2PY503"))
        if isinstance(node, ast.Subscript) and not (isinstance(node.value, ast.Name) and node.value.id == "args"):
            problems.append(error("compile", "sandbox rejected subscript", node.lineno, node.col_offset, "Q2PY505"))
    return problems


def _attribute_reason(node: ast.Attribute) -> str | None:
    """Allow only the attribute shapes the code generator emits.

    Nested attributes and dunder names are how a program reaches
    ``function.__globals__`` and the host builtins.
    """
    if node.attr.startswith("_"):
        return f"sandbox rejected attribute {node.attr}"
    if not isinstance(node.value, ast.Name):
        return "sandbox rejected nested attribute access"
    base = node.value.id
    if base == "env":
        return None if node.attr in {"get", "set", "set_global"} else "sandbox rejected attribute access on env"
    if base == "scope":
        return None if node.attr == "get" else "sandbox rejected attribute access on scope"
    if base != "q":
        return f"sandbox rejected attribute access on {base}"
    import q2py.runtime as runtime

    value = getattr(runtime, node.attr, None)
    if inspect.ismodule(value) or not callable(value):
        return f"sandbox rejected runtime attribute {node.attr}"
    return None


class InProcessExecutor:
    """AST-gated execution in-process. Used to score the authored corpus quickly.

    User-facing runs use SubprocessExecutor. This provider still refuses imports
    and non-allowlisted syntax; it does not apply OS resource limits.
    """

    def run(self, source: str) -> ExecResult:
        problems = validate_generated(source)
        if problems:
            return ExecResult(False, None, "", "sandbox", "generated code rejected", problems)
        import q2py.runtime as runtime

        def blocked(*_args: object, **_kwargs: object) -> object:
            raise PermissionError("generated code cannot import modules")

        safe_builtins = {"True": True, "False": False, "None": None, "__import__": blocked}
        namespace: dict[str, object] = {"q": runtime, "__builtins__": safe_builtins}
        cleaned = source.replace("import q2py.runtime as q\n", "", 1)
        try:
            exec(compile(cleaned, "<q2py>", "exec"), namespace)  # noqa: S102
            program = namespace["q2py_program"]
            if not callable(program):
                raise TypeError("q2py_program is not callable")
            value = program()
        except runtime.QError as exc:
            return ExecResult(False, None, "", exc.signal, str(exc), [error("exec", f"'{exc.signal}: {exc}", code="Q2PY600")])
        except Exception as exc:  # noqa: BLE001
            return ExecResult(False, None, "", "error", f"{type(exc).__name__}: {exc}", [error("exec", str(exc), code="Q2PY613")])
        return ExecResult(True, runtime.canon_value(value), runtime.display(value), None, "", [])


class SubprocessExecutor:
    def __init__(self, timeout: float = 5.0) -> None:
        self.timeout = timeout

    def run(self, source: str) -> ExecResult:
        problems = validate_generated(source)
        if problems:
            return ExecResult(False, None, "", "sandbox", "generated code rejected", problems)
        runner = Path(__file__).with_name("sandbox_main.py")
        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "HOME": "/tmp",
        }
        try:
            completed = subprocess.run(
                [sys.executable, "-I", str(runner)],
                input=source,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return ExecResult(
                False,
                None,
                "",
                "timeout",
                "execution timed out",
                [error("exec", "execution timed out", code="Q2PY610")],
            )
        payload = completed.stdout.strip().splitlines()
        if not payload:
            detail = completed.stderr.strip()[:500] or "sandbox produced no output"
            return ExecResult(False, None, "", "sandbox", detail, [error("exec", detail, code="Q2PY611")])
        try:
            data = json.loads(payload[-1])
        except json.JSONDecodeError:
            return ExecResult(False, None, "", "sandbox", "malformed sandbox output", [error("exec", "malformed sandbox output", code="Q2PY612")])
        if data.get("ok"):
            canon = data.get("canon")
            return ExecResult(True, canon if isinstance(canon, dict) else None, str(data.get("display", "")), None, "", [])
        signal = str(data.get("signal") or "error")
        message = str(data.get("message") or signal)
        return ExecResult(
            False,
            None,
            "",
            signal,
            message,
            [error("exec", f"'{signal}: {message}", code="Q2PY600")],
        )


def runner_source() -> str:
    return textwrap.dedent(
        """
        # The subprocess entry point lives in sandbox_main.py.
        """
    )
