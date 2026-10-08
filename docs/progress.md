# Progress

## Month arithmetic (corpus 1.3.0)

Month literals were already parsed and classified partial because no arithmetic was claimed. Integer offsets now shift the month, including year rollover, and subtracting two months returns the month count as a long. A float offset raises `type`. Timestamp arithmetic is still partial.

`PYTHONPATH=src python -m q2py.score` after the tests:

- Corpus 1.3.0, hash `5bc6eb245934e3b4`, 255 cases: 95 holdout, 133 dev, 27 coverage.
- Holdout denominator 95. Successes 95. Semantic accuracy 1.0. Wilson 0.9611–1.0.
- Value match 94/94. Signal match 1/1. Runtime returned a value 94/95. Oracle unavailable.
- Dev: 133/133 supported cases matched.

## Floor div, floor mod, and converge limit (corpus 1.2.0)

Three constructs that were already partial:

- `div` and `mod` now use floor division for negative integers. `x = (x div y)*y + (x mod y)`. Zero is still a domain error. Both moved from partial to supported. The protected holdout was not edited. Coverage case `cov-div-neg` previously expected the old domain refusal for `-5 div 2`; that case is not holdout, and its expectation is now long `-3`.
- Unary over still cannot loop forever. It returns a fixed point reached within 1000 steps. Otherwise it raises `limit` (`{neg x}/1`). It stays partial.

Measured with `PYTHONPATH=src python -m q2py.score` and `measure("dev")` / `measure("coverage")` after the tests passed:

- Corpus 1.2.0, hash `2e576da190e9c4cc`, 252 cases: 95 holdout, 130 dev, 27 coverage.
- Holdout denominator 95. Successes 95. Semantic accuracy 1.0. Wilson 0.9611–1.0. Unchanged from 1.1.0.
- Value match 94/94. Signal match 1/1. Runtime returned a value 94/95. Oracle unavailable. `oracle_match_rate` null.
- Dev: 130/130 supported cases matched.
- Coverage: 27/27 matched, including the new zero-division and converge-limit signals.

## Coverage expansion (corpus 1.1.0)

The protected 95 holdout cases were not edited. New cases are dev or coverage. Expected values were written from `docs/q-semantics.md` before scoring.

`PYTHONPATH=src python -m q2py.score` on this tree:

- Corpus 1.1.0, hash `4de1bf18cb00cd6d`, 241 cases: 95 holdout, 123 dev, 23 coverage.
- Holdout denominator 95. Successes 95. Semantic accuracy 1.0. Wilson 0.9611–1.0. Same ratio as corpus 1.0.0.
- Value match 94/94. Signal match 1/1 (`length-signal`). Runtime returned a value 94/95.
- Dev split, scored separately: 123/123 supported cases matched. Semantic accuracy 1.0. Wilson 0.9697–1.0. Parse, translation, compile, and runtime-return rates 1.0. Value match 123/123. No authored signals in that split.
- Coverage split: 23 cases, none unmatched. Three of them are supported signal checks (`domain` for negative `div` and negative `xbar`, `unsupported` for `value` of a string, `domain` for `sqrt -1`). The rest are refusals that emit no Python.
- Oracle remains `oracle-unavailable`. `oracle_match_rate` is null.

Five dev cases were refused on the first score (`101b` boolean vectors, and postfix over/scan on a lambda). The lexer and parser were extended to those published forms. The expectations were not changed. A later score matched them. That is a translator fix, not a corpus edit.

New supported verbs include `prd`, `prds`, `all`, `any`, `mins`, `maxs`, `med`, `var`, `dev`, `iasc`, `idesc`, `floor`, `ceiling`, `signum`, `prev`, `next`, `fills`, `differ`, `group`, `cols`, `key`, `value` (dictionaries), `xbar`, `rotate`, `except`, `inter`, and `union`. Infinity literals compile to a float constant (`1e309`) because Python’s `inf` repr is not a literal. The sandbox allow-list was extended only with the new runtime names.

## Audit (corpus 1.0.0)

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
