"""Execute generated Python behind a replaceable sandbox provider.

The local providers are an AST allow-list plus either an in-process exec or a
short-lived ``python -I`` subprocess. Neither one is a container, a VM, or a
network namespace. Production isolation has to be a different
``SandboxProvider``.
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from q2py.diagnostics import Diagnostic, error
from q2py.sandbox_api import SAFE_RUNTIME_NAMES

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
    ast.Lambda,
    ast.Subscript,
    ast.UnaryOp,
    ast.USub,
}

# Names that must never be resolved, called, or defined in generated code.
_DENIED_NAMES = frozenset(
    {
        "open",
        "eval",
        "exec",
        "compile",
        "globals",
        "locals",
        "vars",
        "getattr",
        "setattr",
        "delattr",
        "hasattr",
        "dir",
        "type",
        "object",
        "super",
        "breakpoint",
        "input",
        "help",
        "memoryview",
        "classmethod",
        "staticmethod",
        "property",
        "isinstance",
        "issubclass",
        "callable",
        "__import__",
        "__builtins__",
        "__loader__",
        "__spec__",
        "os",
        "sys",
        "subprocess",
        "socket",
        "importlib",
        "pathlib",
        "shutil",
        "ctypes",
        "builtins",
        "pickle",
        "marshal",
        "resource",
        "mmap",
        "pty",
    }
)

# Generator and frame internals that are not dunder names.
_DENIED_ATTRS = frozenset(
    {
        "gi_frame",
        "gi_code",
        "gi_yieldfrom",
        "cr_frame",
        "cr_code",
        "ag_frame",
        "ag_code",
        "f_globals",
        "f_locals",
        "f_back",
        "f_code",
        "f_builtins",
        "tb_frame",
        "tb_next",
        "tb_lineno",
    }
)

_ENV_ATTRS = frozenset({"get", "set", "set_global"})
_GENERATED_FUNCTION = re.compile(r"_lam\d+\Z")


class SandboxProvider(Protocol):
    """Run generated Python. A container or VM runner can replace the local ones."""

    def run(self, source: str) -> ExecResult: ...


# Pipeline code still imports this name.
Executor = SandboxProvider


@dataclass
class ExecResult:
    ok: bool
    canon: dict[str, object] | None
    display: str
    signal: str | None
    message: str
    diagnostics: list[Diagnostic]


def child_environment() -> dict[str, str]:
    """Environment for the subprocess runner. Parent secrets are not copied."""
    return {
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "HOME": "/tmp",
    }


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
            continue
        problems.extend(_check_node(node))
    return problems


def _check_node(node: ast.AST) -> list[Diagnostic]:
    found: list[Diagnostic] = []
    if isinstance(node, ast.Import):
        names = [alias.name for alias in node.names]
        if names != ["q2py.runtime"]:
            found.append(error("compile", "sandbox rejected import", node.lineno, node.col_offset, "Q2PY502"))
    elif isinstance(node, ast.Name) and _denied_name(node.id):
        found.append(error("compile", f"sandbox rejected name {node.id}", node.lineno, node.col_offset, "Q2PY504"))
    elif isinstance(node, ast.FunctionDef) and not _allowed_function(node.name):
        found.append(error("compile", f"sandbox rejected function {node.name}", node.lineno, node.col_offset, "Q2PY506"))
    elif isinstance(node, ast.Attribute):
        reason = _attribute_reason(node)
        if reason:
            found.append(error("compile", reason, node.lineno, node.col_offset, "Q2PY503"))
    elif isinstance(node, ast.Subscript):
        reason = _subscript_reason(node)
        if reason:
            found.append(error("compile", reason, node.lineno, node.col_offset, "Q2PY505"))
    elif isinstance(node, ast.Call) and not isinstance(node.func, (ast.Attribute, ast.Lambda)):
        found.append(error("compile", "sandbox rejected call", node.lineno, node.col_offset, "Q2PY507"))
    return found


def _denied_name(name: str) -> bool:
    return name in _DENIED_NAMES or name.startswith("__")


def _allowed_function(name: str) -> bool:
    return name == "q2py_program" or _GENERATED_FUNCTION.fullmatch(name) is not None


def _attribute_reason(node: ast.Attribute) -> str | None:
    if node.attr.startswith("_") or node.attr in _DENIED_ATTRS or node.attr in _DENIED_NAMES:
        return f"sandbox rejected attribute {node.attr}"
    if not isinstance(node.value, ast.Name):
        return "sandbox rejected nested attribute access"
    base = node.value.id
    if base == "env":
        return None if node.attr in _ENV_ATTRS else "sandbox rejected attribute access on env"
    if base == "scope":
        return None if node.attr == "get" else "sandbox rejected attribute access on scope"
    if base != "q":
        return f"sandbox rejected attribute access on {base}"
    if node.attr not in SAFE_RUNTIME_NAMES:
        return f"sandbox rejected runtime attribute {node.attr}"
    return None


def _subscript_reason(node: ast.Subscript) -> str | None:
    if not isinstance(node.value, ast.Name) or node.value.id != "args":
        return "sandbox rejected subscript"
    if not isinstance(node.slice, ast.Constant) or not isinstance(node.slice.value, int):
        return "sandbox rejected subscript"
    return None


def _blocked_import(*_args: object, **_kwargs: object) -> object:
    raise PermissionError("generated code cannot import modules")


def _sandbox_builtins() -> dict[str, object]:
    return {"__import__": _blocked_import}


def _execute(source: str, facade: object) -> ExecResult:
    import q2py.runtime as runtime

    problems = validate_generated(source)
    if problems:
        return ExecResult(False, None, "", "sandbox", "generated code rejected", problems)
    namespace: dict[str, object] = {"q": facade, "__builtins__": _sandbox_builtins()}
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
    canon = runtime.canon_value(value)
    if not isinstance(canon, dict):
        return ExecResult(False, None, "", "error", "runtime result was not canonical JSON", [error("exec", "bad canon", code="Q2PY614")])
    return ExecResult(True, canon, str(runtime.display(value)), None, "", [])


class InProcessExecutor:
    """AST-gated execution in the studio process.

    Scoring uses this provider. It does not apply rlimits and it shares the
    host process, so a bug below the AST gate would see the host. User-facing
    runs use ``SubprocessExecutor``.
    """

    def run(self, source: str) -> ExecResult:
        from q2py.sandbox_api import build_facade

        return _execute(source, build_facade())


class SubprocessExecutor:
    """``python -I`` with a stripped environment, CPU and address-space limits, and a timeout.

    This is not a container. The child can still use the host network
    namespace if it gets past the AST gate.
    """

    def __init__(self, timeout: float = 5.0) -> None:
        self.timeout = timeout

    def run(self, source: str) -> ExecResult:
        problems = validate_generated(source)
        if problems:
            return ExecResult(False, None, "", "sandbox", "generated code rejected", problems)
        runner = Path(__file__).with_name("sandbox_main.py")
        try:
            completed = subprocess.run(
                [sys.executable, "-I", str(runner)],
                input=source,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=child_environment(),
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
