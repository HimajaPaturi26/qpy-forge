"""Versioned HTTP API for Q2Py Studio."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from q2py import __version__
from q2py.corpus import load_cases, meta
from q2py.db import get_event, list_events, list_snapshots, record_event, save_snapshot
from q2py.metrics import measure
from q2py.oracle import oracle_status
from q2py.pipeline import translate, validate

app = FastAPI(title="Q2Py Studio", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_MAX_SOURCE = 100_000


class SourceBody(BaseModel):
    source: str = Field(min_length=1, max_length=_MAX_SOURCE)


class ValidateBody(BaseModel):
    source: str = Field(min_length=1, max_length=_MAX_SOURCE)
    case_id: str | None = None


def _case(case_id: str) -> dict[str, Any]:
    for case in load_cases():
        if case["id"] == case_id:
            return case
    raise HTTPException(status_code=404, detail="corpus case not found")


@app.get("/api/v1/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "version": __version__}


@app.get("/api/v1/status")
def status() -> dict[str, Any]:
    return {
        "version": __version__,
        "oracle": oracle_status(),
        "corpus": meta(),
        "sandbox": {
            "user_runs": "subprocess",
            "provider": "SubprocessExecutor",
            "boundary": "ast-allowlist-plus-subprocess",
            "container": False,
            "limits": {"timeout_seconds": 5, "cpu_seconds": 3, "address_space_bytes": 2_500_000_000},
        },
        "support_levels": ["supported", "partial", "unsupported", "oracle-unavailable"],
    }


@app.post("/api/v1/translate")
def translate_source(body: SourceBody) -> dict[str, Any]:
    result = translate(body.source)
    payload = result.to_dict()
    record_event("translate", body.source, payload["stages"].get("codegen", ""), result.support, payload)
    return payload


@app.post("/api/v1/validate")
def validate_source(body: ValidateBody) -> dict[str, Any]:
    expected = None
    expected_signal = None
    if body.case_id:
        case = _case(body.case_id)
        expected = case.get("expected")
        expected_signal = case.get("expected_signal")
    result = validate(body.source, expected, expected_signal)
    payload = result.to_dict()
    record_event("validate", body.source, result.comparison, result.translation.support, payload)
    return payload


@app.get("/api/v1/corpus")
def corpus(split: str | None = None) -> dict[str, Any]:
    cases = load_cases()
    if split:
        cases = [case for case in cases if case["split"] == split]
    return {"meta": meta(), "cases": cases}


@app.get("/api/v1/examples")
def examples() -> dict[str, Any]:
    cases = [case for case in load_cases() if case["split"] in {"dev", "holdout"}][:12]
    return {"examples": [{"id": case["id"], "source": case["source"], "support": case["support"]} for case in cases]}


@app.get("/api/v1/metrics")
def metrics() -> dict[str, Any]:
    report = measure("holdout")
    save_snapshot(report)
    public = {key: value for key, value in report.items() if key != "rows"}
    public["history"] = list_snapshots()
    return public


@app.get("/api/v1/history")
def history(limit: int = 50) -> dict[str, Any]:
    return {"events": list_events(min(limit, 200))}


@app.get("/api/v1/history/{event_id}")
def history_item(event_id: int) -> dict[str, Any]:
    event = get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event not found")
    return event
