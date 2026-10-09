"use client";

import { useEffect, useState } from "react";
import { Notice, PageHeader } from "@/components/ui/notice";
import { Button } from "@/components/ui/button";
import { formatRate, oracleSummary } from "@/lib/format";
import { api } from "@/lib/api";
import type { MetricsReport, StatusPayload } from "@/lib/types";

function Metric({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <tr className="border-t border-line">
      <th className="py-2 pr-4 text-left font-normal text-muted">{label}</th>
      <td className="py-2 pr-4 font-medium tabular-nums">{value}</td>
      <td className="py-2 text-muted">{hint}</td>
    </tr>
  );
}

export default function DashboardPage() {
  const [report, setReport] = useState<MetricsReport | null>(null);
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    setError(null);
    Promise.all([api<MetricsReport>("/api/v1/metrics"), api<StatusPayload>("/api/v1/status")])
      .then(([metrics, nextStatus]) => {
        setReport(metrics);
        setStatus(nextStatus);
      })
      .catch((err: unknown) => {
        setReport(null);
        setStatus(null);
        setError(err instanceof Error ? err.message : "Metrics request failed");
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, []);

  const oracle = report ? oracleSummary(report.oracle) : null;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Accuracy"
        lede="Supported holdout agreement with hand-authored expectations, including authored signals. Partial and unsupported cases are excluded. This is not a live q-oracle result and does not measure arbitrary q."
        actions={
          <Button variant="outline" onClick={load} disabled={loading}>
            {loading ? "Measuring" : "Re-measure"}
          </Button>
        }
      />
      {loading && !report ? <p className="text-sm text-muted">Scoring the holdout corpus</p> : null}
      {error ? <Notice tone="error">{error}</Notice> : null}
      {report && oracle ? (
        <Notice tone="warn">
          q oracle {oracle.title.toLowerCase()}: {oracle.detail} Oracle agreement {formatRate(report.oracle_match_rate)}.
        </Notice>
      ) : null}
      {report && report.sample_size === 0 ? (
        <Notice>The holdout split has no supported cases, so agreement is undefined</Notice>
      ) : null}
      {report ? (
        <>
          <section className="overflow-x-auto">
            <table className="w-full min-w-[36rem] text-left text-sm">
              <thead className="text-xs text-muted">
                <tr>
                  <th className="py-2 pr-4 font-medium">Measure</th>
                  <th className="py-2 pr-4 font-medium">Result</th>
                  <th className="py-2 font-medium">Basis</th>
                </tr>
              </thead>
              <tbody>
            <Metric
              label="Supported holdout agreement"
              value={formatRate(report.semantic_accuracy)}
              hint={`${report.successes} of ${report.sample_size} supported holdout cases · corpus ${report.corpus_version}`}
            />
            <Metric
              label="Wilson 95% interval"
              value={`${formatRate(report.wilson_low)} to ${formatRate(report.wilson_high)}`}
              hint="Interval for the supported holdout agreement above"
            />
            <Metric
              label="Project target"
              value={formatRate(report.target)}
              hint={report.target_met ? "This measurement meets the project target" : "This measurement is below the project target"}
            />
            <Metric
              label="Runtime returned a value"
              value={formatRate(report.runtime_success_rate)}
              hint="Supported holdout cases whose sandbox run returned a value"
            />
            <Metric label="Parse rate" value={formatRate(report.parse_rate)} hint="Supported holdout cases that parsed" />
            <Metric
              label="Translation rate"
              value={formatRate(report.translation_rate)}
              hint="Supported holdout cases that emitted Python"
            />
            <Metric label="Compile rate" value={formatRate(report.compile_rate)} hint="Supported holdout cases that compiled" />
            <Metric
              label="Value match"
              value={formatRate(report.value_match_rate)}
              hint={`${report.value_successes} of ${report.value_sample_size} authored value comparisons`}
            />
            <Metric
              label="Signal match"
              value={formatRate(report.signal_match_rate)}
              hint={`${report.signal_successes} of ${report.signal_sample_size} authored signal comparisons`}
            />
              </tbody>
            </table>
          </section>
          <p className="font-mono text-xs text-muted">
            {report.corpus_version} · {report.corpus_hash} · {report.split} · {report.commit} · {report.corpus_counts.all}{" "}
            cases ({report.corpus_counts.holdout} holdout, {report.corpus_counts.dev} dev, {report.corpus_counts.coverage}{" "}
            coverage)
          </p>
          <section>
            <h2 className="text-lg font-medium">Development split</h2>
            <p className="mt-2 text-sm leading-6 text-muted">
              Dev agreement {formatRate(report.dev_measurement.semantic_accuracy)} on {report.dev_measurement.successes} of{" "}
              {report.dev_measurement.sample_size} supported dev cases. Wilson {formatRate(report.dev_measurement.wilson_low)} to{" "}
              {formatRate(report.dev_measurement.wilson_high)}. Runtime returned a value{" "}
              {formatRate(report.dev_measurement.runtime_success_rate)}. Value match{" "}
              {formatRate(report.dev_measurement.value_match_rate)} ({report.dev_measurement.value_successes} of{" "}
              {report.dev_measurement.value_sample_size}). Signal match {formatRate(report.dev_measurement.signal_match_rate)}{" "}
              ({report.dev_measurement.signal_successes} of {report.dev_measurement.signal_sample_size}). Dev cases are not
              part of the holdout denominator.
            </p>
          </section>
          {report.expected_signals.length ? (
            <section>
              <h2 className="text-lg font-medium">Authored signals</h2>
              <p className="mt-2 text-sm text-muted">
                These cases match when execution raises the authored signal. They count in holdout agreement and signal
                match. They do not count as a returned value.
              </p>
              <ul className="mt-3 space-y-2 text-sm">
                {report.expected_signals.map((item) => (
                  <li key={item.id} className="surface px-3 py-2">
                    <p className="font-medium">
                      {item.id} · signal {item.signal ?? "Not measured"} · {item.matched ? "Matched" : "Not matched"}
                    </p>
                    <pre className="mt-1 overflow-auto text-xs">{item.source}</pre>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
          <section>
            <h2 className="text-lg font-medium">Construct registry</h2>
            <p className="mt-1 text-sm text-muted">
              These lists are the documented registry. Membership is not the holdout agreement.
            </p>
            <div className="mt-3 grid gap-4 lg:grid-cols-3">
              <div className="surface p-3">
                <h3 className="text-sm font-medium">Supported ({report.registry.supported.length})</h3>
                <ul className="mt-2 max-h-64 space-y-1 overflow-auto text-sm">
                  {report.registry.supported.map((feature) => (
                    <li key={feature}>{feature}</li>
                  ))}
                </ul>
              </div>
              <div className="surface p-3">
                <h3 className="text-sm font-medium">Partial ({report.registry.partial.length})</h3>
                <ul className="mt-2 max-h-64 space-y-2 overflow-auto text-sm">
                  {report.registry.partial.map((item) => (
                    <li key={item.feature}>
                      <span className="font-medium">{item.feature}</span>
                      <span className="block text-muted">{item.note}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="surface p-3">
                <h3 className="text-sm font-medium">Unsupported ({report.registry.unsupported.length})</h3>
                <ul className="mt-2 max-h-64 space-y-2 overflow-auto text-sm">
                  {report.registry.unsupported.map((item) => (
                    <li key={item.feature}>
                      <span className="font-medium">{item.feature}</span>
                      <span className="block text-muted">{item.note}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </section>
          <section>
            <h2 className="text-lg font-medium">Holdout construct coverage</h2>
            <p className="mt-1 text-sm text-muted">
              Features are those the translator recorded on each supported holdout case, not the author tags in the
              corpus file.
            </p>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full min-w-[32rem] text-left text-sm">
                <thead className="text-muted">
                  <tr>
                    <th className="py-2 pr-3 font-medium">Feature</th>
                    <th className="py-2 pr-3 font-medium">Matched</th>
                    <th className="py-2 pr-3 font-medium">Cases</th>
                    <th className="py-2 font-medium">Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {report.constructs.map((row) => (
                    <tr key={row.feature} className="border-t border-line">
                      <td className="py-2 pr-3">{row.feature}</td>
                      <td className="py-2 pr-3 tabular-nums">{row.matched}</td>
                      <td className="py-2 pr-3 tabular-nums">{row.n}</td>
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
                <p className="mt-2 text-sm text-muted">No failing supported holdout cases in this measurement</p>
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
              <h2 className="text-lg font-medium">Failing cases</h2>
              {report.top_failures.length === 0 ? (
                <p className="mt-2 text-sm text-muted">None in this measurement</p>
              ) : (
                <ul className="mt-2 space-y-2 text-sm">
                  {report.top_failures.map((item) => (
                    <li key={item.id} className="surface px-3 py-2">
                      <p className="font-medium">{item.id}</p>
                      <p className="text-muted">{item.failure}</p>
                      <pre className="mt-1 overflow-auto text-xs">{item.source}</pre>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>
          <section>
            <h2 className="text-lg font-medium">Measurement history</h2>
            <p className="mt-1 text-sm text-muted">
              {status
                ? status.persistence.durable
                  ? status.persistence.note
                  : `These snapshots use the API history store. ${status.persistence.note}`
                : "Persistence was not loaded with this measurement"}
            </p>
            {report.history.length === 0 ? (
              <p className="mt-2 text-sm text-muted">No snapshots are stored in this API process</p>
            ) : (
              <ul className="mt-2 space-y-1 text-sm">
                {report.history.map((item) => (
                  <li key={item.id} className="flex flex-wrap gap-x-4 gap-y-1 border-t border-line py-2">
                    <span>{item.created_at}</span>
                    <span className="tabular-nums">{formatRate(item.semantic_accuracy)}</span>
                    <span className="text-muted">n={item.sample_size ?? "Not measured"}</span>
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
