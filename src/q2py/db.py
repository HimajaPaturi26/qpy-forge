"""SQLite persistence for translation history and metric snapshots."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_SCHEMA = """
create table if not exists events (
  id integer primary key,
  created_at text not null,
  kind text not null,
  source text,
  status text,
  support text,
  payload text not null
);
create table if not exists metric_snapshots (
  id integer primary key,
  created_at text not null,
  corpus_version text not null,
  corpus_hash text not null,
  commit_sha text,
  payload text not null
);
"""


def db_path() -> Path:
    override = os.environ.get("Q2PY_DB")
    path = Path(override) if override else Path("data") / "q2py.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def _now() -> str:
    return datetime.now(UTC).isoformat()


def record_event(kind: str, source: str, status: str, support: str, payload: dict[str, Any]) -> int:
    with connect() as conn:
        cursor = conn.execute(
            "insert into events (created_at, kind, source, status, support, payload) values (?, ?, ?, ?, ?, ?)",
            (_now(), kind, source[:4000], status, support, json.dumps(payload)),
        )
        row_id = cursor.lastrowid
        if row_id is None:
            raise RuntimeError("sqlite insert did not return a row id")
        return int(row_id)


def list_events(limit: int = 50) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "select id, created_at, kind, source, status, support from events order by id desc limit ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_event(event_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("select * from events where id = ?", (event_id,)).fetchone()
    if row is None:
        return None
    data = dict(row)
    data["payload"] = json.loads(data["payload"])
    return data


def save_snapshot(report: dict[str, Any]) -> int:
    stored = {key: value for key, value in report.items() if key != "rows"}
    with connect() as conn:
        cursor = conn.execute(
            "insert into metric_snapshots (created_at, corpus_version, corpus_hash, commit_sha, payload) values (?, ?, ?, ?, ?)",
            (_now(), str(report.get("corpus_version")), str(report.get("corpus_hash")), str(report.get("commit")), json.dumps(stored)),
        )
        row_id = cursor.lastrowid
        if row_id is None:
            raise RuntimeError("sqlite insert did not return a row id")
        return int(row_id)


def list_snapshots(limit: int = 20) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "select id, created_at, corpus_version, corpus_hash, commit_sha, payload from metric_snapshots order by id desc limit ?",
            (limit,),
        ).fetchall()
    history = []
    for row in rows:
        payload = json.loads(row["payload"])
        history.append(
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "corpus_version": row["corpus_version"],
                "corpus_hash": row["corpus_hash"],
                "commit": row["commit_sha"],
                "semantic_accuracy": payload.get("semantic_accuracy"),
                "sample_size": payload.get("sample_size"),
                "target_met": payload.get("target_met"),
            }
        )
    return history
