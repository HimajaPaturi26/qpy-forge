"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { oracleSummary } from "@/lib/format";
import type { StatusPayload } from "@/lib/types";

export function HomeStatus() {
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<StatusPayload>("/api/v1/status")
      .then(setStatus)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Status request failed"));
  }, []);

  if (!status && !error) {
    return <p className="text-sm text-muted">Checking status</p>;
  }
  if (error || !status) {
    return (
      <p className="text-sm text-muted">
        Status request failed.{" "}
        <Link href="/settings" className="text-paper underline decoration-line underline-offset-4">
          Open status
        </Link>
      </p>
    );
  }

  const oracle = oracleSummary(status.oracle);
  return (
    <dl className="text-sm">
      <div className="grid gap-1 border-t border-line py-3 sm:grid-cols-[11rem_1fr] sm:gap-6">
        <dt className="text-muted">q oracle</dt>
        <dd>
          {oracle.title} — {oracle.detail}
        </dd>
      </div>
      <div className="grid gap-1 border-t border-line py-3 sm:grid-cols-[11rem_1fr] sm:gap-6">
        <dt className="text-muted">Holdout agreement</dt>
        <dd>Authored expectations on the Accuracy page. Not a live q-oracle comparison.</dd>
      </div>
      <div className="grid gap-1 border-t border-line py-3 sm:grid-cols-[11rem_1fr] sm:gap-6">
        <dt className="text-muted">History</dt>
        <dd>
          {status.persistence.durable ? "Durable" : "Non-durable"} {status.persistence.engine}. {status.persistence.note}
        </dd>
      </div>
      <div className="grid gap-1 border-t border-b border-line py-3 sm:grid-cols-[11rem_1fr] sm:gap-6">
        <dt className="text-muted">Execution</dt>
        <dd>
          {status.sandbox.boundary}
          {status.sandbox.container ? "; container reported" : "; not container-isolated"}
        </dd>
      </div>
    </dl>
  );
}
