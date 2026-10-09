# Deployment

The studio is two processes. The Next.js app is a website. The FastAPI app is a long-running container: it scores the corpus, writes SQLite, and runs generated Python in a subprocess. It is not a Vercel function. The q binary is optional and is never executed.

History is SQLite. `/api/v1/status` reports `persistence.durable: false`. A container without a mounted volume loses history when it is replaced. Do not describe that history as persistent.

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

The browser calls `/api` on the Next.js origin. The Next.js server proxies that to `Q2PY_API_ORIGIN`. When the variable is unset and `VERCEL` is unset, the proxy uses `http://127.0.0.1:43118`.

`Q2PY_DB` overrides the SQLite path. `Q2PY_CORPUS` overrides `corpus/cases.json`. `Q2PY_Q_BIN` names a q binary for the status page only. `Q2PY_CORS_ORIGINS` is a comma-separated list, or `*`.

Templates: `.env.example` and `apps/web/.env.example`.

## Tests

```sh
.venv/bin/ruff check src tests
.venv/bin/mypy --strict src/q2py
.venv/bin/pytest
cd apps/web && npm test && npm run lint && npm run build
```

## API container

```sh
docker build -t q2py-studio .
docker run --rm -p 43118:43118 q2py-studio
```

The image sets `Q2PY_CORPUS=/app/corpus/cases.json` and `Q2PY_DB=/data/q2py.sqlite`. `/data` is a volume mount point. Without a mount, the file is ephemeral. Health check: `GET /api/v1/health`.

q is not installed in the image. The sandbox is still `python -I` plus the AST allow-list. It is not a nested container.

### Fly.io

`fly.toml` is the API service. From a logged-in Fly account:

```sh
fly launch --no-deploy --copy-config
fly deploy
curl -fsS "https://<your-app>.fly.dev/api/v1/health"
```

Attach a volume only if history must survive a restart, and keep `Q2PY_DB` on that volume. This repository has not been deployed to Fly from here.

### Render

`render.yaml` is a Docker web service on the free plan. The free disk is ephemeral. Connect the repo in the Render dashboard and use that blueprint, or create a web service with the Dockerfile, health check path `/api/v1/health`, and the env vars in the file. This repository has not been deployed to Render from here.

## Website on Vercel

The Next.js app lives in `apps/web`. In the Vercel project set Root Directory to `apps/web`. Set `Q2PY_API_ORIGIN` to the public API origin, for example `https://<your-app>.fly.dev`, with no trailing slash. A loopback value is ignored on Vercel and `/api` returns 503.

After the API health URL responds, open the Vercel site and translate `2*3+4` in Studio. The browser should stay on the Vercel host; the Next.js server calls the API.

## Live Vercel deployment

Checked on 2026-10-09 after `vercel deploy --prod`:

- Website: https://qpy-forge.vercel.app
- API: https://qpy-forge-api.vercel.app
- `GET /api/v1/health` on the API and through the website both returned `{"status":"ok","version":"0.1.0"}`.
- `POST /api/v1/validate` with `2*3+4` through the website executed and returned long `14`.
- Oracle status was `oracle-unavailable`. SQLite history is not durable on this host.

`himajapaturi.in` is attached to the `qpy-forge` project and is not serving the site until Hostinger DNS is changed. Vercel’s verify command recommended two A records for `@` (`216.198.79.1` and `64.29.17.1`) and a CNAME for `www` (`2f0659adc4688a4f.vercel-dns-017.com`). Nameservers were left on Hostinger.
