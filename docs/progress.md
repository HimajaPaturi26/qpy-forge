# Progress

- Engine: lexer through sandbox, API, and corpus scorer are implemented.
- Quality gate on this tree: `ruff check src tests`, `mypy --strict src/q2py`, and `pytest` (98 passed).
- Holdout measurement from `python -m q2py.score` on this tree: corpus `1.0.0` hash `c055fa1a54e35247`, sample size 95, successes 95, semantic accuracy 1.0, Wilson 95% interval about 0.9611–1.0, runtime success rate about 0.9895, oracle match rate null, oracle status `oracle-unavailable`.
- That accuracy is agreement with hand-authored expectations. q was not installed, so it is not a kdb+ audit.
- Frontend studio, validation, dashboard, corpus, history, docs, and status pages read the API. They do not hard-code the rates above.
- Headless Chrome walked landing, studio translate, studio refusal (`1|2`), validate (`2*3+4` value-match 14), dashboard, corpus, history, status, 404, and a 390px studio layout. Screenshots are in `docs/screenshots/`. The dashboard showed semantic accuracy 100.0%, sample size 95, runtime success 98.9%, oracle match —, and Oracle: unavailable.
- Oracle execution is detection only. A present `q` binary is still not invoked.
