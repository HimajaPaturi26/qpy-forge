#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$root"
PYTHONPATH=src .venv/bin/uvicorn q2py.api:app --host 127.0.0.1 --port 43118 &
api_pid=$!
trap 'kill "$api_pid"' EXIT INT TERM
cd "$root/apps/web"
exec npx next dev --hostname 127.0.0.1 --port 43117
