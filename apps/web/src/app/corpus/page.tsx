"use client";

import { useEffect, useState } from "react";
import { SupportBadge } from "@/components/support-badge";
import { api } from "@/lib/api";
import type { CorpusCase } from "@/lib/types";

export default function CorpusPage() {
  const [cases, setCases] = useState<CorpusCase[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [split, setSplit] = useState("all");

  useEffect(() => {
    const query = split === "all" ? "" : `?split=${encodeURIComponent(split)}`;
    api<{ cases: CorpusCase[] }>(`/api/v1/corpus${query}`)
      .then((payload) => setCases(payload.cases))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Could not load the corpus"));
  }, [split]);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Corpus</h1>
        <p className="mt-1 max-w-2xl text-sm text-muted">
          Holdout cases with declared support “supported” are the accuracy denominator. Coverage cases document
          refusals and partial behavior and are excluded from that rate.
        </p>
      </div>
      <label className="text-sm">
        <span className="mr-2 text-muted">Split</span>
        <select
          className="h-9 rounded-md border border-line bg-ink px-2"
          value={split}
          onChange={(event) => {
            setCases(null);
            setSplit(event.target.value);
          }}
        >
          <option value="all">All</option>
          <option value="holdout">Holdout</option>
          <option value="dev">Dev</option>
          <option value="coverage">Coverage</option>
        </select>
      </label>
      {error ? (
        <p className="text-sm text-bad" role="alert">
          {error}
        </p>
      ) : null}
      {!cases && !error ? <p className="text-sm text-muted">Loading cases…</p> : null}
      {cases && cases.length === 0 ? <p className="text-sm text-muted">No cases in this split.</p> : null}
      {cases && cases.length > 0 ? (
        <ul className="divide-y divide-line rounded-lg border border-line">
          {cases.map((item) => (
            <li key={item.id} className="space-y-2 px-4 py-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium">{item.id}</span>
                <SupportBadge support={item.support} />
                <span className="text-xs text-muted">{item.split}</span>
              </div>
              <pre className="overflow-auto font-mono text-sm">{item.source}</pre>
              {item.features?.length ? <p className="text-xs text-muted">{item.features.join(", ")}</p> : null}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
