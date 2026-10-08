"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { formatRate } from "@/lib/format";
import { api } from "@/lib/api";
import type { MetricsReport } from "@/lib/types";

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-lg border border-line p-4">
      <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-2 text-2xl font-semibold tabular-nums">{value}</p>
    </article>
  );
}

export default function DashboardPage() {
  const [report, setReport] = useState<MetricsReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    setError(null);
    api<MetricsReport>("/api/v1/metrics")
      .then(setReport)
      .catch((err: unknown) => {
        setReport(null);
        setError(err instanceof Error ? err.message : "Metrics request failed");
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Accuracy</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted">
            Semantic accuracy is the share of holdout cases declared supported whose result matches a hand-authored
            expectation. It is not a live kdb+ audit.
          </p>
        </div>
        <Button variant="outline" onClick={load} disabled={loading}>
          {loading ? "Measuring…" : "Re-measure"}
        </Button>
      </div>
      {loading && !report ? <p className="text-sm text-muted">Scoring the holdout corpus…</p> : null}
      {error ? (
        <p className="rounded-md border border-bad/40 bg-bad/10 px-3 py-2 text-sm text-bad" role="alert">
          {error}
        </p>
      ) : null}
      {report && report.sample_size === 0 ? (
        <p className="text-sm text-muted">The holdout split has no supported cases, so accuracy is undefined.</p>
      ) : null}
      {report ? (
        <>
          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Metric label="Semantic accuracy" value={formatRate(report.semantic_accuracy)} />
            <Metric label="Wilson 95% interval" value={`${formatRate(report.wilson_low)} – ${formatRate(report.wilson_high)}`} />
            <Metric label="Target" value={formatRate(report.target)} />
            <Metric label="Target met" value={report.target_met ? "Yes" : "No"} />
            <Metric label="Sample size" value={String(report.sample_size)} />
            <Metric label="Successes" value={String(report.successes)} />
            <Metric label="Parse rate" value={formatRate(report.parse_rate)} />
            <Metric label="Translation rate" value={formatRate(report.translation_rate)} />
            <Metric label="Compile rate" value={formatRate(report.compile_rate)} />
            <Metric label="Runtime success" value={formatRate(report.runtime_success_rate)} />
            <Metric label="Value match" value={formatRate(report.value_match_rate)} />
            <Metric label="Oracle match" value={formatRate(report.oracle_match_rate)} />
          </section>
          <section className="rounded-lg border border-line p-4 text-sm">
            <p>
              Oracle: {report.oracle.available ? report.oracle.status : "unavailable"}. {report.oracle.reason}
            </p>
            <p className="mt-2 text-muted">
              Corpus {report.corpus_version} · {report.corpus_hash} · split {report.split} · commit {report.commit}
            </p>
            <p className="mt-1 text-muted">
              Cases: {report.corpus_counts.all} total, {report.corpus_counts.holdout} holdout, {report.corpus_counts.dev}{" "}
              dev, {report.corpus_counts.coverage} coverage.
            </p>
          </section>
          <section>
            <h2 className="text-lg font-medium">Construct coverage</h2>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full min-w-[32rem] text-left text-sm">
                <thead className="text-muted">
                  <tr>
                    <th className="py-2 font-medium">Feature</th>
                    <th className="py-2 font-medium">Matched</th>
                    <th className="py-2 font-medium">N</th>
                    <th className="py-2 font-medium">Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {report.constructs.map((row) => (
                    <tr key={row.feature} className="border-t border-line">
                      <td className="py-2">{row.feature}</td>
                      <td className="py-2 tabular-nums">{row.matched}</td>
                      <td className="py-2 tabular-nums">{row.n}</td>
                      <td className="py-2 tabular-nums">{formatRate(row.rate)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          <section className="grid gap-6 lg:grid-cols-2">
            <div>
              <h2 className="text-lg font-medium">Failure categories</h2>
              {report.failure_categories.length === 0 ? (
                <p className="mt-2 text-sm text-muted">No failing supported holdout cases in this measurement.</p>
              ) : (
                <ul className="mt-2 space-y-1 text-sm">
                  {report.failure_categories.map((item) => (
                    <li key={item.category}>
                      {item.category}: {item.count}
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div>
              <h2 className="text-lg font-medium">Top failing cases</h2>
              {report.top_failures.length === 0 ? (
                <p className="mt-2 text-sm text-muted">None in this run.</p>
              ) : (
                <ul className="mt-2 space-y-2 text-sm">
                  {report.top_failures.map((item) => (
                    <li key={item.id} className="rounded-md border border-line px-3 py-2">
                      <p className="font-medium">{item.id}</p>
                      <p className="text-muted">{item.failure}</p>
                      <pre className="mt-1 overflow-auto font-mono text-xs">{item.source}</pre>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>
          <section>
            <h2 className="text-lg font-medium">Run history</h2>
            {report.history.length === 0 ? (
              <p className="mt-2 text-sm text-muted">No snapshots stored yet.</p>
            ) : (
              <ul className="mt-2 space-y-1 text-sm">
                {report.history.map((item) => (
                  <li key={item.id} className="flex flex-wrap gap-x-4 gap-y-1 border-t border-line py-2">
                    <span>{item.created_at}</span>
                    <span className="tabular-nums">{formatRate(item.semantic_accuracy)}</span>
                    <span className="text-muted">n={item.sample_size ?? "—"}</span>
                    <span className="text-muted">{item.commit}</span>
                    <span className="text-muted">{item.corpus_version}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      ) : null}
    </div>
  );
}
