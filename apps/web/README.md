# Q2Py Forge web

Next.js UI for the studio. The server route `/api` proxies to `Q2PY_API_ORIGIN`. When that variable is unset and `VERCEL` is unset, the target is `http://127.0.0.1:43118`. On Vercel the variable must be the public API origin; loopback is rejected.

```sh
npm ci
npm run dev -- --hostname 127.0.0.1 --port 43117
npm test
npm run lint
npm run build
```
