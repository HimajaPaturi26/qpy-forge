#!/bin/sh
# Long-running API. Hosts set PORT; local runs keep 43118.
port="${PORT:-43118}"
exec uvicorn q2py.api:app --host 0.0.0.0 --port "$port"
