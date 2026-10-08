"""Regression tests for the generated-Python sandbox.

Each case is an attack class. Rejection has to happen before the payload
runs, so a successful test does not read the host file or the host environment.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from q2py.pipeline import translate
from q2py.sandbox import InProcessExecutor, SubprocessExecutor, child_environment, validate_generated
from q2py.sandbox_api import SAFE_RUNTIME_NAMES, build_facade

_EXECUTORS = [InProcessExecutor(), SubprocessExecutor()]


def _program(body: str) -> str:
    return "def q2py_program():\n" + "\n".join(f"    {line}" for line in body.splitlines()) + "\n"


def _rejected(source: str) -> None:
    problems = validate_generated(source)
    assert problems, source
    for executor in _EXECUTORS:
        result = executor.run(source)
        assert result.ok is False
        assert result.signal == "sandbox"
        assert result.canon is None


@pytest.mark.parametrize(
    "source",
    [
        "def q2py_program():\n    return q.long.__globals__\n",
        "def q2py_program():\n    return q.long.__code__\n",
        "def q2py_program():\n    return q.long.__closure__\n",
        "def q2py_program():\n    return q.long.__builtins__\n",
        "def q2py_program():\n    return q.__dict__\n",
        "def q2py_program():\n    return q.__class__\n",
        "def q2py_program():\n    return q.Env.__mro__\n",
        "def q2py_program():\n    return q.long.gi_frame\n",
        "def q2py_program():\n    return q.long.f_globals\n",
        "def q2py_program():\n    return q.long.cr_frame\n",
    ],
)
def test_dunder_and_frame_attributes_are_rejected(source: str) -> None:
    _rejected(source)


@pytest.mark.parametrize(
    "source",
    [
        _program("return globals()"),
        _program("return locals()"),
        _program("return vars()"),
        _program("return getattr(q, 'long')"),
        _program("return eval('1')"),
        _program("return exec('1')"),
        _program("return compile('1', '<x>', 'eval')"),
        _program("return __import__('os')"),
    ],
)
def test_reflection_and_dynamic_execution_are_rejected(source: str) -> None:
    _rejected(source)


@pytest.mark.parametrize(
    "source",
    [
        "import os\n" + _program("return os.getcwd()"),
        "import sys\n" + _program("return sys.path"),
        "import socket\n" + _program("return socket.socket()"),
        "import subprocess\n" + _program("return subprocess.run(['id'])"),
        "import importlib\n" + _program("return importlib.import_module('os')"),
        "from os import system\n" + _program("return system('id')"),
        "from pathlib import Path\n" + _program("return Path('/etc/passwd').read_text()"),
    ],
)
def test_imports_are_rejected(source: str) -> None:
    _rejected(source)


def test_open_and_host_file_are_rejected(tmp_path: Path) -> None:
    probe = tmp_path / "secret.txt"
    probe.write_text("HOSTFILE-MARKER", encoding="utf-8")
    source = _program(f"return open({str(probe)!r}).read()")
    _rejected(source)
    assert probe.read_text(encoding="utf-8") == "HOSTFILE-MARKER"


def test_environment_is_not_readable_and_not_forwarded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("Q2PY_AUDIT_SECRET", "top-secret-value")
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.example")
    _rejected(_program("return os.environ['Q2PY_AUDIT_SECRET']"))
    _rejected(_program("return __import__('os').environ['Q2PY_AUDIT_SECRET']"))
    child = child_environment()
    assert "Q2PY_AUDIT_SECRET" not in child
    assert "HTTP_PROXY" not in child
    assert "top-secret-value" not in " ".join(child.values())
    parent_keys = set(os.environ)
    assert "Q2PY_AUDIT_SECRET" in parent_keys
    assert set(child) <= {"PYTHONNOUSERSITE", "PYTHONDONTWRITEBYTECODE", "LANG", "LC_ALL", "HOME"}


@pytest.mark.parametrize(
    "source",
    [
        _program("import socket\n    s = socket.create_connection(('example.com', 80))"),
        "import socket\n" + _program("return socket.create_connection(('example.com', 80))"),
        _program("return q.socket"),
        _program("return subprocess.run(['id'])"),
        _program("return os.system('id')"),
    ],
)
def test_network_and_subprocess_names_are_rejected(source: str) -> None:
    _rejected(source)


@pytest.mark.parametrize(
    "source",
    [
        _program("return q.long.__globals__['__builtins__']['open']"),
        _program("f = q.long\n    return f.__globals__"),
        _program("return (q.long).__code__"),
        _program("return q.math"),
        _program("return q.cast"),
        _program("return q.canon_value"),
        _program("return q.filter_table"),
        _program("return q.QError"),
        _program("return args['__builtins__']"),
        _program("return {'a': 1}['a']"),
    ],
)
def test_attribute_chains_subscripts_and_hidden_runtime_names_are_rejected(source: str) -> None:
    _rejected(source)


def test_runtime_facade_exposes_only_the_safe_api() -> None:
    import q2py.runtime as runtime
    import q2py.values as values

    facade = build_facade()
    for name in SAFE_RUNTIME_NAMES:
        assert callable(getattr(facade, name)), name
    for hidden in ("math", "cast", "QError", "Atom", "filter_table", "canon_value", "display", "open", "system"):
        with pytest.raises(AttributeError):
            getattr(facade, hidden)
    banned = {"os", "subprocess", "socket", "importlib", "ctypes", "pathlib", "shutil", "urllib", "http"}
    assert banned.isdisjoint(vars(runtime))
    assert banned.isdisjoint(vars(values))


def test_translated_programs_still_pass_the_gate() -> None:
    from q2py.corpus import load_cases

    checked = 0
    for case in load_cases():
        translated = translate(str(case["source"]))
        if not translated.python:
            continue
        assert validate_generated(translated.python) == [], translated.source
        checked += 1
    assert checked >= 90


def test_subprocess_still_runs_a_supported_program() -> None:
    from q2py.pipeline import validate

    result = validate("2*3+4", {"t": "long", "v": 14})
    assert result.matched is True
    assert "top-secret-value" not in result.display
