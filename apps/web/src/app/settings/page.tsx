"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { StatusPayload } from "@/lib/types";

export default function SettingsPage() {
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<StatusPayload>("/api/v1/status")
      .then(setStatus)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Status request failed"));
  }, []);

  return (
    <div className="max-w-3xl space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Status</h1>
        <p className="mt-1 text-sm text-muted">Runtime configuration for this process. There are no accounts.</p>
      </div>
      {!status && !error ? <p className="text-sm text-muted">Checking the API…</p> : null}
      {error ? (
        <p className="text-sm text-bad" role="alert">
          {error}. Start the API on port 43118, or set Q2PY_API_ORIGIN for the Next.js rewrite.
        </p>
      ) : null}
      {status ? (
        <dl className="grid gap-4 text-sm sm:grid-cols-2">
          <div className="rounded-lg border border-line p-4">
            <dt className="text-muted">Version</dt>
            <dd className="mt-1 font-medium">{status.version}</dd>
          </div>
          <div className="rounded-lg border border-line p-4">
            <dt className="text-muted">Oracle</dt>
            <dd className="mt-1 font-medium">{status.oracle.available ? status.oracle.status : "Oracle: unavailable"}</dd>
            <dd className="mt-1 text-muted">{status.oracle.reason}</dd>
          </div>
          <div className="rounded-lg border border-line p-4">
            <dt className="text-muted">Corpus</dt>
            <dd className="mt-1 font-medium">
              {status.corpus.version} · {status.corpus.hash}
            </dd>
            <dd className="mt-1 text-muted">Target {status.corpus.target}</dd>
          </div>
          <div className="rounded-lg border border-line p-4">
            <dt className="text-muted">Sandbox</dt>
            <dd className="mt-1 font-medium">{status.sandbox.user_runs}</dd>
            <dd className="mt-1 text-muted">
              {status.sandbox.boundary}. {status.sandbox.container ? "Container." : "Not a container."} Timeout{" "}
              {status.sandbox.limits.timeout_seconds}s · cpu {status.sandbox.limits.cpu_seconds}s
            </dd>
          </div>
        </dl>
      ) : null}
    </div>
  );
}
