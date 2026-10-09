# Q2Py Forge

Q2Py Forge translates supported Q/kdb+ expressions into Python through an inspectable compiler pipeline. It shows the generated Python, runs that Python under a restricted local executor, and compares the result with expectations stored in this repository. Unsupported syntax returns a diagnostic and does not invent Python.

This is an independent engineering project by [Himaja Paturi](https://www.linkedin.com/in/himajapaturi/).

A kdb+ license is not required to develop, test, run, or deploy this project. When the `q` binary is absent, the API and the Accuracy page report the oracle as unavailable. That is not a completed oracle check.

The public site is [https://qpy-forge.vercel.app](https://qpy-forge.vercel.app). The API is [https://qpy-forge-api.vercel.app](https://qpy-forge-api.vercel.app). `himajapaturi.in` is attached in the website project and is not serving this app.

## Measured holdout result

This is agreement with hand-authored expectations in `corpus/cases.json`. It is not a live q audit. Re-run the scorer after you clone. The `commit` field is whatever `git rev-parse --short HEAD` was at measurement time.

On corpus 1.7.0, `PYTHONPATH=src python -m q2py.score` reported:

| Metric | Value |
| --- | --- |
| Corpus | 1.7.0, hash `bc7d4165a39036a9` |
| Cases | 282 total: 95 holdout, 148 dev, 39 coverage |
| Holdout sample (declared support `supported`) | 95 |
| Holdout expectation matches | 95 |
| Semantic accuracy | 1.0 on 95/95 supported holdout |
| Wilson 95% interval | 0.9611 – 1.0 |
| Target | 0.90 (met on this holdout measurement) |
| Parse / translation / compile | 1.0 |
| Value match | 1.0 on 94 value comparisons |
| Signal match | 1.0 on 1 authored signal (`length-signal`, source `1 2+1 2 3`) |
| Runtime returned a value | 0.9895 (94/95) |
| Dev split | 148/148 supported dev cases matched (1.0). This is not the headline accuracy. |
| Coverage split | 39 cases, 0 unmatched |
| Oracle match | null |
| Oracle | `oracle-unavailable` (`q` binary not found) |

The protected holdout ratio is unchanged from corpus 1.0.0. The runtime rate is 94/95 because `length-signal` is expected to raise `length`. That match is a semantic success and not a returned value. Partial cases and unsupported coverage cases are outside the accuracy denominator.

Expected values were written in this repository. The each-right case note records that its expectation was checked against the published each-left rule after a mismatch. See `docs/limitations.md`. Later constructs, including `xexp`, have regression tests and are not part of that 95-case holdout.

## Run

```sh
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cd apps/web && npm ci && cd ../..
sh scripts/dev.sh
```

- Studio: http://127.0.0.1:43117
- API: http://127.0.0.1:43118, prefix `/api/v1`

The website and the API are separate processes. The Next.js route handler proxies `/api` to `Q2PY_API_ORIGIN`. Locally, when that variable and `VERCEL` are unset, the target is `http://127.0.0.1:43118`.

The live API is a Vercel Python function. Its SQLite file is on ephemeral disk, and status reports that history is not durable. `Dockerfile`, `fly.toml`, and `render.yaml` are alternative hosts and are not the current public deployment. Details are in `docs/deployment.md`. Templates are `.env.example` and `apps/web/.env.example`.

Pages: landing, translation studio, validation, accuracy, corpus, history, documentation, status, plus 404 and 500.

## Test

```sh
.venv/bin/ruff check src tests
.venv/bin/mypy --strict src/q2py
.venv/bin/pytest
cd apps/web && npm test && npm run lint && npm run build
```

GitHub Actions runs the same Python and web checks on push. The web job uses Node 22 and `npm ci`, so `apps/web/package-lock.json` has to match that npm.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/health` | Process up |
| GET | `/api/v1/status` | Version, oracle, corpus, sandbox limits |
| POST | `/api/v1/translate` | `{ "source" }` |
| POST | `/api/v1/validate` | `{ "source", "case_id"? }` |
| GET | `/api/v1/corpus` | Authored cases |
| GET | `/api/v1/examples` | Short example list |
| GET | `/api/v1/metrics` | Scores the holdout and stores a snapshot |
| GET | `/api/v1/history` | Recent events |

## Screenshots

Taken from the running app in headless Chrome. The dashboard image is from corpus 1.1.0, so its counts are older than the table above.

![Landing](docs/screenshots/landing.png)

![Studio translation of 2*3+4](docs/screenshots/studio-result.png)

![Studio refusal captured before greater was implemented](docs/screenshots/studio-refused.png)

![Holdout accuracy](docs/screenshots/dashboard.png)

## Layout

- `src/q2py` — lexer, parser, IR, codegen, runtime, sandbox, corpus, API
- `corpus/cases.json` — independent expectations
- `apps/web` — Next.js studio
- `docs/` — architecture, methodology, constructs, limitations, types, security, deployment
