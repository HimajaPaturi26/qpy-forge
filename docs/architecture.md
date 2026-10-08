# Architecture

```
q source
  lexer → tokens
  parser → AST
  semantic analysis → IR + diagnostics + support label
  codegen → Python (skipped when unsupported)
  sandbox AST check
  executor → canonical JSON
  comparison with an authored expectation
  metrics
```

`q2py.pipeline.translate` and `q2py.pipeline.validate` are the only entry points the API uses. Each stage is recorded as `ok`, `error`, `skipped`, or `pending`.

Support is one of `supported`, `partial`, or `unsupported`. Oracle availability is a separate status, `oracle-unavailable` when q cannot be used.

Generated modules look like:

```python
import q2py.runtime as q

def q2py_program():
    env = q.Env()
    ...
```

The runner removes that import and injects the runtime module, so generated code cannot import anything else. `__import__` is replaced. The subprocess executor starts `python -I`, drops the parent environment except a small allow-list, and sets `RLIMIT_CPU`, `RLIMIT_AS`, and `RLIMIT_FSIZE`.

Corpus scoring calls `InProcessExecutor`, which uses the same AST allow-list and restricted builtins. It does not apply rlimits. The HTTP validate endpoint uses `SubprocessExecutor`.

SQLite (`Q2PY_DB`, default `data/q2py.sqlite`) stores translation events and metric snapshots. There is no account system.

The Next.js app rewrites `/api/*` to the FastAPI process (`Q2PY_API_ORIGIN`, default `http://127.0.0.1:43118`).
