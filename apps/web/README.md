# Q2Py Studio web

Next.js UI for the studio. The API is proxied from `/api` to `Q2PY_API_ORIGIN` (default `http://127.0.0.1:43118`).

```sh
npm ci
npm run dev -- --hostname 127.0.0.1 --port 43117
npm test
npm run lint
npm run build
```
