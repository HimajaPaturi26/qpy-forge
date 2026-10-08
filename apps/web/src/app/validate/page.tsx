"use client";

import { useEffect, useState } from "react";
import { JsonBlock } from "@/components/json-block";
import { SupportBadge } from "@/components/support-badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { CorpusCase, Validation } from "@/lib/types";

export default function ValidatePage() {
  const [cases, setCases] = useState<CorpusCase[] | null>(null);
  const [caseId, setCaseId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Validation | null>(null);

  useEffect(() => {
    api<{ cases: CorpusCase[] }>("/api/v1/corpus")
      .then((payload) => {
        setCases(payload.cases);
        const first = payload.cases.find((item) => item.support === "supported");
        if (first) {
          setCaseId(first.id);
        }
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Could not load the corpus"));
  }, []);

  const selected = cases?.find((item) => item.id === caseId) ?? null;

  async function run() {
    if (!selected) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const payload = await api<Validation>("/api/v1/validate", {
        method: "POST",
        body: JSON.stringify({ source: selected.source, case_id: selected.id }),
      });
      setResult(payload);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Validation failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Validation</h1>
        <p className="mt-1 max-w-2xl text-sm text-muted">
          Each case carries an expected value or signal written into the corpus. The translator does not author that
          expectation.
        </p>
      </div>
      {!cases && !error ? <p className="text-sm text-muted">Loading corpus cases…</p> : null}
      {error ? (
        <p className="rounded-md border border-bad/40 bg-bad/10 px-3 py-2 text-sm text-bad" role="alert">
          {error}
        </p>
      ) : null}
      {cases && cases.length === 0 ? <p className="text-sm text-muted">The corpus has no cases.</p> : null}
      {cases && cases.length > 0 ? (
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-sm">
            <span className="mb-1 block text-muted">Corpus case</span>
            <select
              className="h-9 min-w-64 rounded-md border border-line bg-ink px-2"
              value={caseId}
              onChange={(event) => {
                setCaseId(event.target.value);
                setResult(null);
              }}
            >
              {cases.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.id} · {item.split} · {item.support}
                </option>
              ))}
            </select>
          </label>
          <Button onClick={() => void run()} disabled={busy || !selected}>
            {busy ? "Running…" : "Validate case"}
          </Button>
        </div>
      ) : null}
      {selected ? (
        <section className="space-y-2">
          <div className="flex items-center gap-2">
            <SupportBadge support={selected.support} />
            <span className="text-xs text-muted">{selected.split}</span>
          </div>
          <pre className="overflow-auto rounded-md border border-line bg-black/30 p-3 font-mono text-sm">{selected.source}</pre>
        </section>
      ) : null}
      {result ? (
        <section className="space-y-3 text-sm">
          <p>
            Comparison <span className="font-medium">{result.comparison}</span>
            {result.matched === null ? "" : result.matched ? " · matched the authored expectation" : " · did not match"}
          </p>
          <p className="font-mono">{result.display || "No display value."}</p>
          {result.signal ? <p>Runtime signal: {result.signal}</p> : null}
          <JsonBlock
            value={{
              expected: result.expected,
              expected_signal: result.expected_signal,
              canon: result.canon,
              oracle: result.oracle,
            }}
          />
          {result.diagnostics.length ? (
            <ul className="space-y-2">
              {result.diagnostics.map((item, index) => (
                <li key={`${item.code}-${index}`} className="rounded-md border border-line px-3 py-2">
                  {item.code}: {item.message}
                </li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
