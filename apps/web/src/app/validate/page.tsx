"use client";

import { useEffect, useState } from "react";
import { JsonBlock } from "@/components/json-block";
import { SupportBadge } from "@/components/support-badge";
import { Notice, PageHeader } from "@/components/ui/notice";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { comparisonLabel, stageLabel } from "@/lib/format";
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
      <PageHeader
        title="Validate"
        lede="Compare a corpus case with the authored value or signal on that record. Not a live q-oracle check."
      />
      {!cases && !error ? <p className="text-sm text-secondary">Loading corpus cases</p> : null}
      {error ? <Notice tone="error">{error}</Notice> : null}
      {cases && cases.length === 0 ? <Notice>The corpus has no cases</Notice> : null}
      {cases && cases.length > 0 ? (
        <div className="flex flex-wrap items-end gap-3">
          <label className="block min-w-0 w-full text-sm sm:w-auto">
            <span className="mb-1 block text-secondary">Corpus case</span>
            <select
              className="field w-full max-w-full sm:w-auto sm:min-w-64"
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
            {busy ? "Running" : "Validate case"}
          </Button>
        </div>
      ) : null}
      {selected ? (
        <section className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <SupportBadge support={selected.support} />
            <span className="text-xs text-secondary">{selected.split}</span>
            <span className="text-xs text-secondary">
              {selected.expected_signal
                ? `Authored signal ${selected.expected_signal}`
                : selected.expected
                  ? "Authored value"
                  : "No authored expectation on this record"}
            </span>
          </div>
          <pre className="overflow-auto rounded-md border border-line bg-ink p-3 font-mono text-sm">{selected.source}</pre>
        </section>
      ) : null}
      {result ? (
        <section className="space-y-3 text-sm">
          <p>{comparisonLabel(result.comparison)}</p>
          <p>
            Execution {result.executed ? "returned a value" : "did not return a value"}. Compile{" "}
            {stageLabel(result.stages.compile)}.
          </p>
          {result.executed ? (
            <p className="font-mono">{result.display || "No display value"}</p>
          ) : (
            <p className="text-secondary">Execution has not produced a value.</p>
          )}
          {result.signal ? <p>Runtime signal: {result.signal}</p> : null}
          <p className="text-secondary">
            {result.oracle.available ? result.oracle.reason : `The q oracle is unavailable. ${result.oracle.reason}`}
          </p>
          <JsonBlock
            value={{
              expected: result.expected,
              expected_signal: result.expected_signal,
              canon: result.canon,
            }}
          />
          {result.diagnostics.length ? (
            <ul className="space-y-2">
              {result.diagnostics.map((item, index) => (
                <li key={`${item.code}-${index}`} className="surface px-3 py-2">
                  <span className="font-mono text-xs text-secondary">
                    {item.code} · {item.stage} · {item.line}:{item.col}
                  </span>
                  <p className="mt-1">{item.message}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-secondary">No diagnostics were returned.</p>
          )}
        </section>
      ) : selected ? (
        <p className="text-sm text-secondary">Not run</p>
      ) : null}
    </div>
  );
}
