# Deployment

The API is a long-running process with a SQLite file and a subprocess sandbox. It is not a serverless function.

## Local

```sh
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cd apps/web && npm ci
cd ../..
sh scripts/dev.sh
```

- Studio: http://127.0.0.1:43117
- API: http://127.0.0.1:43118

`Q2PY_DB` overrides the SQLite path. `Q2PY_Q_BIN` names a q binary if you want the status endpoint to notice it. The binary is not executed.

`Q2PY_API_ORIGIN` tells Next.js where to proxy `/api`.

## Tests

```sh
.venv/bin/ruff check src tests
.venv/bin/mypy --strict src/q2py
.venv/bin/pytest
cd apps/web && npm test && npm run lint && npm run build
```

## Container

The Dockerfile runs the API only:

```sh
docker build -t q2py-studio .
docker run --rm -p 43118:43118 q2py-studio
```

Serve `apps/web` separately with `npm run build && npm run start`, and set `Q2PY_API_ORIGIN` to the API. q is not installed in the image.

## GitHub Actions

`.github/workflows/ci.yml` runs the Python gate and the Next.js test, lint, and build. It does not need a kdb+ license.
