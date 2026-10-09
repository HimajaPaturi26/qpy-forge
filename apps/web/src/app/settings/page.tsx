"use client";

import { useEffect, useState } from "react";
import { Notice, PageHeader } from "@/components/ui/notice";
import { api } from "@/lib/api";
import { oracleSummary } from "@/lib/format";
import type { StatusPayload } from "@/lib/types";

export default function SettingsPage() {
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<StatusPayload>("/api/v1/status")
      .then(setStatus)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Status request failed"));
  }, []);

  const oracle = status ? oracleSummary(status.oracle) : null;

  return (
    <div className="max-w-3xl space-y-5">
      <PageHeader
        title="Status"
        lede="Health and capability for this API process. There are no accounts. Values appear only after the status request succeeds."
      />
      {!status && !error ? <p className="text-sm text-muted">Checking the API</p> : null}
      {error ? (
        <Notice tone="error">
          {error}. The website could not read the API. Locally the API listens on port 43118. In production set
          Q2PY_API_ORIGIN to the public API URL.
        </Notice>
      ) : null}
      {status && oracle ? (
        <dl className="grid gap-4 text-sm sm:grid-cols-2">
          <div className="surface p-4">
            <dt className="text-muted">API</dt>
            <dd className="mt-1 font-medium">Responded</dd>
            <dd className="mt-1 text-muted">Version {status.version}</dd>
          </div>
          <div className="surface p-4">
            <dt className="text-muted">Q oracle</dt>
            <dd className="mt-1 font-medium">{oracle.title}</dd>
            <dd className="mt-1 text-muted">{oracle.detail}</dd>
          </div>
          <div className="surface p-4">
            <dt className="text-muted">Corpus</dt>
            <dd className="mt-1 font-medium">
              {status.corpus.version} · {status.corpus.hash}
            </dd>
            <dd className="mt-1 text-muted">
              Project target {status.corpus.target}
              {status.corpus.counts
                ? ` · ${status.corpus.counts.all} cases (${status.corpus.counts.holdout} holdout, ${status.corpus.counts.dev} dev, ${status.corpus.counts.coverage} coverage)`
                : ""}
            </dd>
          </div>
          <div className="surface p-4">
            <dt className="text-muted">History storage</dt>
            <dd className="mt-1 font-medium">{status.persistence.durable ? "Durable" : "Not durable"}</dd>
            <dd className="mt-1 text-muted">{status.persistence.note}</dd>
          </div>
          <div className="surface p-4 sm:col-span-2">
            <dt className="text-muted">Sandbox</dt>
            <dd className="mt-1 font-medium">
              {status.sandbox.user_runs} · {status.sandbox.provider}
            </dd>
            <dd className="mt-1 text-muted">
              {status.sandbox.boundary}. {status.sandbox.container ? "Reported as a container" : "Not a container"}.
              Timeout {status.sandbox.limits.timeout_seconds}s · CPU {status.sandbox.limits.cpu_seconds}s · address space{" "}
              {status.sandbox.limits.address_space_bytes} bytes. Corpus scoring uses the same AST allow-list in-process
              and does not apply these resource limits.
            </dd>
          </div>
        </dl>
      ) : null}
    </div>
  );
}
