# Validation methodology

## What is measured

Semantic accuracy is the number of holdout cases with declared support `supported` whose result matches the case, divided by the number of those cases.

A match is:

- canonical JSON equality with `expected`, or
- a runtime signal equal to `expected_signal`, or
- for coverage cases with `expect_support: unsupported`, a refusal that emits no Python.

`runtime_success_rate` counts cases that returned a value. An authored signal match is a semantic success and is not a runtime success. `value_match_rate` uses only value comparisons. `signal_match_rate` uses only signal comparisons. Construct rates use the features the translator recorded, not the tags written next to the case.

Partial cases and unsupported coverage cases are not in the denominator.

The 95 holdout cases that existed at corpus 1.0.0 are unchanged. Corpus 1.1.0 adds dev and coverage cases around them. `python -m q2py.score` still scores the holdout. The metrics API also scores the dev split and returns it as `dev_measurement`. That number is not the headline accuracy.

A dashboard accuracy figure has to show its successes, its sample size, and the corpus version. Corpus coverage, the construct registry, runtime-return rate, signal matches, and oracle availability are separate.

## What is not measured

The translator does not write expected values. `q2py.corpus.load_cases` rejects provenance that starts with `generated-by-translator`.

These expectations were written from published q evaluation rules by the same project that implements the runtime. Agreement can share a blind spot. It is not a substitute for running the same programs in q. When q is absent, `oracle_match_rate` is null and the oracle status is `oracle-unavailable`.

## Uncertainty

`q2py.metrics.wilson` reports a 95% Wilson interval. `target_met` is true only when the point estimate is at least `0.90`. The target is not itself a result.

## Failure taxonomy

`refused-supported`, `refused`, `parse`, `translation`, `compile`, `runtime`, `value`, and `unsafe-guess`.

## How to reproduce

```sh
PYTHONPATH=src python -m q2py.score
```

The command prints the report without per-case rows. The `commit` field is `git rev-parse --short HEAD` at measurement time.
