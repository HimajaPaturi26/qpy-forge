"""Versioned HTTP API for Q2Py Studio."""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.responses import Response

from q2py import __version__
from q2py.corpus import load_cases, meta
from q2py.db import get_event, list_events, list_snapshots, record_event, save_snapshot
from q2py.metrics import measure
from q2py.oracle import oracle_status
from q2py.pipeline import translate, validate

app = FastAPI(title="Q2Py Studio", version=__version__)


def _cors_origins() -> list[str]:
    raw = os.environ.get("Q2PY_CORS_ORIGINS", "*").strip()
    if raw == "*":
        return ["*"]
    return [item.strip() for item in raw.split(",") if item.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

_MAX_SOURCE = 100_000
_MAX_BODY = 200_000


@app.middleware("http")
async def limit_request_body(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    declared = request.headers.get("content-length")
    if declared is not None and declared.isdigit() and int(declared) > _MAX_BODY:
        return JSONResponse(status_code=413, content={"detail": "request body is too large"})
    return await call_next(request)


@app.exception_handler(Exception)
async def unhandled_error(_request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else "request failed"
        return JSONResponse(status_code=exc.status_code, content={"detail": detail})
    if isinstance(exc, RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": "invalid request"})
    return JSONResponse(status_code=500, content={"detail": "internal error"})


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
        "persistence": {
            "engine": "sqlite",
            "durable": False,
            "note": "History and metric snapshots are SQLite rows in this process. A container without a mounted volume loses that file when it is replaced. This response does not claim the disk is durable.",
        },
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


_SUMMARY_KEYS = (
    "split",
    "sample_size",
    "successes",
    "semantic_accuracy",
    "wilson_low",
    "wilson_high",
    "parse_rate",
    "translation_rate",
    "compile_rate",
    "runtime_success_rate",
    "value_match_rate",
    "value_sample_size",
    "value_successes",
    "signal_match_rate",
    "signal_sample_size",
    "signal_successes",
)


@app.get("/api/v1/metrics")
def metrics() -> dict[str, Any]:
    report = measure("holdout")
    save_snapshot(report)
    public = {key: value for key, value in report.items() if key != "rows"}
    dev = measure("dev")
    public["dev_measurement"] = {key: dev[key] for key in _SUMMARY_KEYS}
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
