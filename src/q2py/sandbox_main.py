"""Subprocess entry point. Reads generated Python on stdin and prints JSON."""

from __future__ import annotations

import json
import resource
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Cap CPU and address space before importing the runtime (which imports Polars).
_AS = 2_500_000_000
try:
    resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
    resource.setrlimit(resource.RLIMIT_AS, (_AS, _AS))
    resource.setrlimit(resource.RLIMIT_FSIZE, (8_000_000, 8_000_000))
except (ValueError, OSError):
    pass

import q2py.runtime as q  # noqa: E402


def main() -> None:
    import sys

    source = sys.stdin.read().replace("import q2py.runtime as q\n", "", 1)

    def _blocked_import(*_args: object, **_kwargs: object) -> object:
        raise PermissionError("generated code cannot import modules")

    safe_builtins = {
        "True": True,
        "False": False,
        "None": None,
        "__import__": _blocked_import,
    }
    namespace: dict[str, object] = {"q": q, "__builtins__": safe_builtins}
    try:
        exec(compile(source, "<q2py>", "exec"), namespace)  # noqa: S102
        program = namespace["q2py_program"]
        if not callable(program):
            raise TypeError("q2py_program is not callable")
        value = program()
        json.dump({"ok": True, "canon": q.canon_value(value), "display": q.display(value)}, sys.stdout)
    except q.QError as exc:
        json.dump({"ok": False, "signal": exc.signal, "message": str(exc)}, sys.stdout)
    except Exception as exc:  # noqa: BLE001
        json.dump(
            {"ok": False, "signal": "error", "message": f"{type(exc).__name__}: {exc}", "trace": traceback.format_exc()[-800:]},
            sys.stdout,
        )


if __name__ == "__main__":
    main()
