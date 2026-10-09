"""Subprocess entry point. Reads generated Python on stdin and prints one JSON line.

The parent supplies a stripped environment. This process is not a container:
it shares the host network namespace and can still read files the OS allows
if the AST gate is bypassed.
"""

from __future__ import annotations

import json
import os
import resource
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
runtime_site = os.environ.get("Q2PY_RUNTIME_SITE", "")
if runtime_site:
    sys.path.insert(0, runtime_site)

_AS = 2_500_000_000
try:
    resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
    resource.setrlimit(resource.RLIMIT_AS, (_AS, _AS))
    resource.setrlimit(resource.RLIMIT_FSIZE, (8_000_000, 8_000_000))
    # RLIMIT_NPROC also counts threads. Polars needs worker threads, so a
    # zero process limit prevents the runtime from importing. Fork is blocked
    # by the AST gate, not by this rlimit.
except (ValueError, OSError):
    pass

import q2py.runtime as runtime  # noqa: E402
from q2py.sandbox_api import build_facade  # noqa: E402


def main() -> None:
    source = sys.stdin.read().replace("import q2py.runtime as q\n", "", 1)

    def blocked(*_args: object, **_kwargs: object) -> object:
        raise PermissionError("generated code cannot import modules")

    namespace: dict[str, object] = {"q": build_facade(), "__builtins__": {"__import__": blocked}}
    try:
        exec(compile(source, "<q2py>", "exec"), namespace)  # noqa: S102
        program = namespace["q2py_program"]
        if not callable(program):
            raise TypeError("q2py_program is not callable")
        value = program()
        json.dump({"ok": True, "canon": runtime.canon_value(value), "display": runtime.display(value)}, sys.stdout)
    except runtime.QError as exc:
        json.dump({"ok": False, "signal": exc.signal, "message": str(exc)}, sys.stdout)
    except Exception as exc:  # noqa: BLE001
        json.dump({"ok": False, "signal": "error", "message": f"{type(exc).__name__}: {exc}"}, sys.stdout)


if __name__ == "__main__":
    main()
