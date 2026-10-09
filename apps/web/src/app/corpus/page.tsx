"use client";

import { useEffect, useState } from "react";
import { SupportBadge } from "@/components/support-badge";
import { Notice, PageHeader } from "@/components/ui/notice";
import { api } from "@/lib/api";
import type { CorpusCase, StatusPayload } from "@/lib/types";

const splits = [
  ["all", "All"],
  ["holdout", "Holdout"],
  ["dev", "Dev"],
  ["coverage", "Coverage"],
] as const;

export default function CorpusPage() {
  const [cases, setCases] = useState<CorpusCase[] | null>(null);
  const [meta, setMeta] = useState<StatusPayload["corpus"] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [split, setSplit] = useState("all");

  useEffect(() => {
    const query = split === "all" ? "" : `?split=${encodeURIComponent(split)}`;
    api<{ cases: CorpusCase[]; meta: StatusPayload["corpus"] }>(`/api/v1/corpus${query}`)
      .then((payload) => {
        setCases(payload.cases);
        setMeta(payload.meta);
        setError(null);
      })
      .catch((err: unknown) => {
        setCases(null);
        setError(err instanceof Error ? err.message : "Could not load the corpus");
      });
  }, [split]);

  return (
    <div className="space-y-5">
      <PageHeader
        title="Corpus"
        lede="Holdout cases declared supported form the agreement denominator. Dev is scored separately. Coverage is excluded from that rate."
      />
      {meta?.counts ? (
        <p className="text-sm text-muted">
          Corpus {meta.version} · {meta.hash} · {meta.counts.all} cases ({meta.counts.holdout} holdout, {meta.counts.dev}{" "}
          dev, {meta.counts.coverage} coverage)
        </p>
      ) : null}
      <label className="text-sm">
        <span className="mr-2 text-muted">Split</span>
        <select
          className="field"
          value={split}
          onChange={(event) => {
            setCases(null);
            setSplit(event.target.value);
          }}
        >
          {splits.map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
      {error ? <Notice tone="error">{error}</Notice> : null}
      {!cases && !error ? <p className="text-sm text-muted">Loading cases</p> : null}
      {cases && cases.length === 0 ? <Notice>No cases in this split</Notice> : null}
      {cases && cases.length > 0 ? (
        <>
          <p className="text-sm text-muted">Showing {cases.length} {split === "all" ? "cases" : `${split} cases`}</p>
          <ul className="divide-y divide-line rounded-md border border-line">
            {cases.map((item) => (
              <li key={item.id} className="space-y-2 px-4 py-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium">{item.id}</span>
                  <SupportBadge support={item.support} />
                  <span className="text-xs text-muted">{item.split}</span>
                </div>
                <pre className="overflow-auto text-sm">{item.source}</pre>
                {item.features?.length ? (
                  <p className="text-xs text-muted">Author tags: {item.features.join(", ")}</p>
                ) : null}
                {item.note ? <p className="text-xs text-muted">{item.note}</p> : null}
              </li>
            ))}
          </ul>
        </>
      ) : null}
    </div>
  );
}
