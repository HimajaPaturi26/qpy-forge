/** Where the Next.js server proxies `/api`. Loopback is only for local development. */

export function apiOrigin(env: { Q2PY_API_ORIGIN?: string; VERCEL?: string }): string | null {
  const configured = env.Q2PY_API_ORIGIN?.trim().replace(/\/$/, "") ?? "";
  const onVercel = Boolean(env.VERCEL);
  if (!configured) {
    return onVercel ? null : "http://127.0.0.1:43118";
  }
  let host = "";
  try {
    const url = new URL(configured);
    if (url.protocol !== "http:" && url.protocol !== "https:") {
      return null;
    }
    host = url.hostname;
  } catch {
    return null;
  }
  const loopback = host === "localhost" || host === "127.0.0.1" || host === "::1";
  if (onVercel && loopback) {
    return null;
  }
  return configured;
}
