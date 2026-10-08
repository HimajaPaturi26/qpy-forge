# Plan

Q2Py Studio translates a documented subset of q into Python and checks the result against hand-authored expected values. A q/kdb+ process is optional and is not required to build, test, or run the studio.

## Decisions

- Python 3.12, FastAPI, Pydantic v2, SQLite, pytest, Hypothesis, ruff, and mypy strict.
- Next.js, TypeScript strict, Tailwind, and CodeMirror. Buttons follow the shadcn variant pattern (`class-variance-authority`) without a second component library.
- Atoms, lists, dictionaries, and functions are plain Python values. Tables also keep a Polars frame for columnar filters. See `docs/type-mapping.md`.
- User execution goes through `Executor`. The default is a restricted subprocess. Corpus scoring uses the same AST allow-list in-process.
- Headline semantic accuracy uses holdout cases whose declared support is `supported`. Partial and unsupported cases are reported separately.
- Expected values live in `corpus/cases.json` and are never produced by the translator.

## Phases

1. Foundation: package, frontend app, CI, docs.
2. Lexer, parser, AST, semantic analysis, IR.
3. Python generation, syntax checks, sandbox.
4. Corpus, comparison, Wilson intervals, construct metrics.
5. Versioned API and SQLite history.
6. Studio: editors, translate, validate, examples, upload, copy, download, inspectors.
7. Landing, validation, dashboard, corpus, history, docs, status, 404, 500.
8. Unit, API, property, and frontend tests.
9. Oracle adapter that reports availability and does not invoke q.
10. Docker image for the API, README, and a measured score.
