# Progress

## Audit (current tree)

The scorer was re-run with `PYTHONPATH=src python -m q2py.score` after the fixes below.

- Corpus 1.0.0, hash `074d3be72b3f44ea`, 99 cases: 95 holdout, 2 dev, 2 coverage.
- Holdout denominator: 95 cases whose declared support is `supported`. Successes 95. Semantic accuracy 1.0. Wilson 95% interval 0.9611–1.0. Target 0.90 met on this run.
- Value comparisons 94/94. Signal comparisons 1/1. Runtime returned a value 94/95.
- The single runtime miss is `length-signal` (`1 2+1 2 3`), authored signal `length`. `matched` is true and `ran` is false.
- Oracle status `oracle-unavailable`. `oracle_match_rate` is null. q is not installed.
- Hash is SHA-256 of the case list with sorted keys, truncated to 16 hex characters. Two loads in one process match. Splits are only `holdout`, `dev`, and `coverage`. Case ids are unique. No source text is shared across splits after the dev-case edit.
- Expected values are read from `corpus/cases.json`. The loader rejects provenance starting with `generated-by-translator`. Scoring calls the current `translate` / `validate` path. Nothing in the scorer writes an expected value.
- The 1.0 result is that ratio. It is not a blind holdout and not a kdb+ audit. The each-right expectation was reconciled with the published each-left rule after the translator disagreed with an earlier expectation. That is recorded on the case.

## Fixes from the audit

- Sandbox: nested attributes, dunder names, and subscripts other than `args[...]` are rejected. A probe of `q.long.__globals__["__builtins__"]["open"]` previously read a host file in-process. Both executors now return signal `sandbox` before execution.
- `select ... where` keeps the original virtual `i`. `select i from t where i=1` had been returning 0.
- `if`, `do`, `while`, `peach`, and literal atom `?` no longer emit Python. They are unsupported refusals.
- Dev case `dev-hello` no longer duplicates holdout source `1+2*3`. Its source is `sum 10 20` with expected long 30. Holdout cases were not edited.
- Metrics: value match and signal match have separate denominators. Construct rates use translator-recorded features. The dashboard names the runtime column “Runtime returned a value” and lists authored signals.
- `not`, `null`, and `neg` are listed with the other implemented verbs. Multi-statement programs record `script`. A comment token records `comment`.

## Still outside the holdout construct table

`flip`, keyed-table literals, and virtual `i` have unit tests and are not separate holdout cases. Partial application (`f[10]` on a dyadic lambda) is holdout case `projection`, and the translator records `apply` rather than `projection` unless an argument is a hole.

## Sandbox hardening

The local executors implement `SandboxProvider`. Generated Python is checked against the AST shapes the translator emits, then run against a facade that only exposes `SAFE_RUNTIME_NAMES`.

Rejected before execution, with regression tests in `tests/test_sandbox.py`: dunder and frame attributes, `globals` / `locals` / `getattr` / `eval` / `exec` / `compile` / `__import__`, imports of `os`, `sys`, `socket`, `subprocess`, `importlib`, and `pathlib`, `open` of a host file, parent environment variables, network and subprocess names, nested attributes, and subscripts other than `args[int]`. The facade does not expose `math`, `cast`, `QError`, `filter_table`, or `canon_value`. Translated corpus programs still pass the gate. `2*3+4` still matches through the subprocess runner.

`RLIMIT_NPROC` of 0 also blocks Polars threads, so it is not used. Fork, the host filesystem, and the host network are not isolated by a namespace. The subprocess sandbox is not a container. See `docs/security.md`.

The holdout corpus and its expected values were not changed.

## Checks run

- `ruff check src tests`
- `mypy --strict src/q2py`
- `pytest` (154 passed, including `tests/test_sandbox.py`)
- `npm test` (3 passed), `npm run lint`, `npm run build` in `apps/web`
- `PYTHONPATH=src python -m q2py.score`
- Headless Chrome walk of the studio, refusal, validation, dashboard, corpus, history, status, 404, and a 390px studio layout. The dashboard showed semantic accuracy 100.0% on 95 cases, value match 100.0% of 94, signal match 100.0% of 1, runtime returned a value 98.9%, and the authored signal `length-signal`. Oracle: unavailable. Corpus hash `074d3be72b3f44ea`. The commit shown on that page was `71f732b`, the HEAD before this audit commit.
- After sandbox hardening: headless Chrome loaded an example, translated it to a `q.mul` program, and the status page showed `ast-allowlist-plus-subprocess` and “Not a container.”
