"""Load the authored corpus and score it. Expected values are read from JSON only."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from q2py.pipeline import validate
from q2py.support import CORPUS_VERSION, TARGET

ROOT = Path(__file__).resolve().parents[2]
CORPUS_PATH = ROOT / "corpus" / "cases.json"


def load_cases(path: Path | None = None) -> list[dict[str, Any]]:
    payload = json.loads((path or CORPUS_PATH).read_text(encoding="utf-8"))
    cases = payload["cases"]
    if not isinstance(cases, list):
        raise ValueError("corpus cases must be a list")
    for case in cases:
        if case.get("provenance", "").startswith("generated-by-translator"):
            raise ValueError(f"case {case.get('id')} has forbidden provenance")
        if "expected" not in case and "expected_signal" not in case and "expect_support" not in case:
            raise ValueError(f"case {case.get('id')} has no independent expectation")
    return cases


def corpus_hash(cases: list[dict[str, Any]] | None = None) -> str:
    raw = json.dumps(cases if cases is not None else load_cases(), sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def score_case(case: dict[str, Any]) -> dict[str, Any]:
    if case.get("expect_support") == "unsupported":
        from q2py.pipeline import translate

        translated = translate(str(case["source"]))
        matched = translated.support == "unsupported" and translated.python == ""
        return {
            "id": case["id"],
            "split": case["split"],
            "declared_support": case["support"],
            "actual_support": translated.support,
            "features": list(translated.features),
            "source": case["source"],
            "parsed": translated.stages.get("parse") == "ok",
            "translated": bool(translated.python),
            "compiled": False,
            "ran": False,
            "matched": matched,
            "comparison": "refused" if matched else "unsafe-guess",
            "signal": None,
            "display": "",
            "failure": None if matched else "unsafe-guess",
            "diagnostics": [item.to_dict() for item in translated.diagnostics],
        }
    from q2py.sandbox import InProcessExecutor

    result = validate(
        str(case["source"]),
        case.get("expected"),
        case.get("expected_signal"),
        executor=InProcessExecutor(),
    )
    stages = result.translation.stages
    parsed = stages.get("parse") == "ok" and stages.get("lex") == "ok"
    produced = bool(result.translation.python)
    compiled = stages.get("compile") == "ok"
    ran = result.executed
    matched = bool(result.matched)
    if result.translation.support == "unsupported" and case.get("support") == "supported":
        failure = "refused-supported"
    elif result.translation.support == "unsupported":
        failure = "refused"
    elif not parsed:
        failure = "parse"
    elif not produced:
        failure = "translation"
    elif not compiled:
        failure = "compile"
    elif result.signal and not matched:
        failure = "runtime"
    elif not matched:
        failure = "value"
    else:
        failure = None
    return {
        "id": case["id"],
        "split": case["split"],
        "declared_support": case["support"],
        "actual_support": result.translation.support,
        "features": list(result.translation.features),
        "source": case["source"],
        "parsed": parsed,
        "translated": produced,
        "compiled": compiled,
        "ran": ran,
        "matched": matched,
        "comparison": result.comparison,
        "signal": result.signal,
        "display": result.display,
        "failure": failure,
        "diagnostics": [item.to_dict() for item in result.diagnostics],
    }


def iter_scores(split: str | None = None) -> list[dict[str, Any]]:
    cases = load_cases()
    if split:
        cases = [case for case in cases if case["split"] == split]
    return [score_case(case) for case in cases]


def meta() -> dict[str, Any]:
    cases = load_cases()
    return {
        "version": CORPUS_VERSION,
        "target": TARGET,
        "hash": corpus_hash(cases),
        "counts": {
            "all": len(cases),
            "holdout": sum(1 for case in cases if case["split"] == "holdout"),
            "dev": sum(1 for case in cases if case["split"] == "dev"),
            "coverage": sum(1 for case in cases if case["split"] == "coverage"),
        },
    }
