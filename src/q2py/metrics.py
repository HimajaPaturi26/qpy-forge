"""Accuracy metrics. Numbers come only from scoring the authored corpus."""

from __future__ import annotations

import math
import subprocess
from typing import Any

from q2py.corpus import iter_scores, meta
from q2py.oracle import oracle_status
from q2py.support import DOCUMENTED_UNSUPPORTED, PARTIAL_FEATURES, PARTIAL_NOTES, SUPPORTED_FEATURES, TARGET


def wilson(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = proportion + z * z / (2 * total)
    margin = z * math.sqrt((proportion * (1 - proportion) + z * z / (4 * total)) / total)
    low = max(0.0, (centre - margin) / denominator)
    high = min(1.0, (centre + margin) / denominator)
    return (low, high)


def _rate(flag: str, rows: list[dict[str, Any]]) -> float | None:
    if not rows:
        return None
    return sum(1 for row in rows if row[flag]) / len(rows)


def _matched_rate(rows: list[dict[str, Any]]) -> float | None:
    if not rows:
        return None
    return sum(1 for row in rows if row["matched"]) / len(rows)


def commit_sha() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    return completed.stdout.strip() or "unknown"


def measure(split: str = "holdout") -> dict[str, Any]:
    info = meta()
    rows = iter_scores(split)
    scoped = [row for row in rows if row["declared_support"] == "supported"]
    value_rows = [row for row in scoped if str(row["comparison"]).startswith("value-")]
    signal_rows = [row for row in scoped if str(row["comparison"]).startswith("signal-")]
    successes = sum(1 for row in scoped if row["matched"])
    low, high = wilson(successes, len(scoped))
    accuracy = (successes / len(scoped)) if scoped else None
    by_construct: dict[str, dict[str, int]] = {}
    for row in scoped:
        for feature in row["features"]:
            bucket = by_construct.setdefault(feature, {"n": 0, "matched": 0})
            bucket["n"] += 1
            if row["matched"]:
                bucket["matched"] += 1
    failures: dict[str, int] = {}
    failing_cases = []
    for row in scoped:
        if row["failure"]:
            failures[row["failure"]] = failures.get(row["failure"], 0) + 1
            failing_cases.append(
                {
                    "id": row["id"],
                    "source": row["source"],
                    "failure": row["failure"],
                    "signal": row["signal"],
                    "display": row["display"],
                }
            )
    oracle = oracle_status()
    return {
        "corpus_version": info["version"],
        "corpus_hash": info["hash"],
        "corpus_counts": info["counts"],
        "split": split,
        "commit": commit_sha(),
        "target": TARGET,
        "sample_size": len(scoped),
        "successes": successes,
        "semantic_accuracy": accuracy,
        "wilson_low": low,
        "wilson_high": high,
        "target_met": bool(accuracy is not None and accuracy >= TARGET),
        "parse_rate": _rate("parsed", scoped),
        "translation_rate": _rate("translated", scoped),
        "compile_rate": _rate("compiled", scoped),
        "runtime_success_rate": _rate("ran", scoped),
        "value_match_rate": _matched_rate(value_rows),
        "value_sample_size": len(value_rows),
        "value_successes": sum(1 for row in value_rows if row["matched"]),
        "signal_match_rate": _matched_rate(signal_rows),
        "signal_sample_size": len(signal_rows),
        "signal_successes": sum(1 for row in signal_rows if row["matched"]),
        "expected_signals": [
            {"id": row["id"], "source": row["source"], "signal": row["signal"], "matched": row["matched"]}
            for row in scoped
            if not row["ran"]
        ],
        "oracle_match_rate": None,
        "oracle": oracle,
        "constructs": [
            {
                "feature": feature,
                "n": bucket["n"],
                "matched": bucket["matched"],
                "rate": bucket["matched"] / bucket["n"] if bucket["n"] else None,
            }
            for feature, bucket in sorted(by_construct.items())
        ],
        "failure_categories": [{"category": key, "count": value} for key, value in sorted(failures.items())],
        "top_failures": failing_cases[:10],
        "registry": {
            "supported": sorted(SUPPORTED_FEATURES),
            "partial": [
                {"feature": feature, "note": PARTIAL_NOTES.get(feature, "")} for feature in sorted(PARTIAL_FEATURES)
            ],
            "unsupported": [{"feature": name, "note": note} for name, note in DOCUMENTED_UNSUPPORTED],
        },
        "rows": rows,
    }
