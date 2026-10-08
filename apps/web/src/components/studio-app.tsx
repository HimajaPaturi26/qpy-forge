"use client";

import { useRef, useState } from "react";
import { QEditor, PythonEditor } from "@/components/editors";
import { JsonBlock } from "@/components/json-block";
import { SupportBadge } from "@/components/support-badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Translation, Validation } from "@/lib/types";

type Example = { id: string; source: string; support: string };
type Panel = "diagnostics" | "output" | "tokens" | "ast" | "ir";

const stages = ["lex", "parse", "semantic", "ir", "codegen", "compile", "exec", "compare"] as const;

export function StudioApp() {
  const [source, setSource] = useState("");
  const [examples, setExamples] = useState<Example[] | null>(null);
  const [busy, setBusy] = useState<"translate" | "validate" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [translation, setTranslation] = useState<Translation | null>(null);
  const [validation, setValidation] = useState<Validation | null>(null);
  const [panel, setPanel] = useState<Panel>("diagnostics");
  const [copied, setCopied] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function loadExamples() {
    setError(null);
    try {
      const payload = await api<{ examples: Example[] }>("/api/v1/examples");
      setExamples(payload.examples);
      if (!source && payload.examples[0]) {
        setSource(payload.examples[0].source);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load examples");
    }
  }

  async function translate() {
    if (!source.trim()) {
      setError("Paste q source, load an example, or upload a .q file.");
      return;
    }
    setBusy("translate");
    setError(null);
    setValidation(null);
    try {
      const result = await api<Translation>("/api/v1/translate", {
        method: "POST",
        body: JSON.stringify({ source }),
      });
      setTranslation(result);
      setPanel("diagnostics");
    } catch (err) {
      setTranslation(null);
      setError(err instanceof Error ? err.message : "Translation failed");
    } finally {
      setBusy(null);
    }
  }

  async function validate() {
    if (!source.trim()) {
      setError("There is no q source to validate.");
      return;
    }
    setBusy("validate");
    setError(null);
    try {
      const result = await api<Validation>("/api/v1/validate", {
        method: "POST",
        body: JSON.stringify({ source }),
      });
      setTranslation(result);
      setValidation(result);
      setPanel("output");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation failed");
    } finally {
      setBusy(null);
    }
  }

  function upload(file: File | undefined) {
    if (!file) {
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      setSource(String(reader.result ?? ""));
      setTranslation(null);
      setValidation(null);
      setError(null);
    };
    reader.onerror = () => setError("Could not read that file.");
    reader.readAsText(file);
  }

  async function copyPython() {
    if (!translation?.python) {
      return;
    }
    await navigator.clipboard.writeText(translation.python);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  function downloadPython() {
    if (!translation?.python) {
      return;
    }
    const blob = new Blob([translation.python], { type: "text/x-python" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "translated.py";
    link.click();
    URL.revokeObjectURL(url);
  }

  const python = translation?.python ?? "";
  const empty = !source.trim() && !translation && !error;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Translation studio</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted">
            Unsupported q is refused. The generated Python is left empty rather than guessed.
          </p>
        </div>
        {translation ? <SupportBadge support={translation.support} /> : null}
      </div>

      <div className="flex flex-wrap gap-2">
        <Button onClick={() => void translate()} disabled={busy !== null}>
          {busy === "translate" ? "Translating…" : "Translate"}
        </Button>
        <Button variant="secondary" onClick={() => void validate()} disabled={busy !== null}>
          {busy === "validate" ? "Validating…" : "Validate"}
        </Button>
        <Button variant="outline" onClick={() => void loadExamples()}>
          Load examples
        </Button>
        <Button variant="outline" onClick={() => fileRef.current?.click()}>
          Upload .q
        </Button>
        <input
          ref={fileRef}
          type="file"
          accept=".q,text/plain"
          className="sr-only"
          aria-label="Upload a q file"
          onChange={(event) => upload(event.target.files?.[0])}
        />
        <Button variant="ghost" onClick={() => void copyPython()} disabled={!python}>
          {copied ? "Copied" : "Copy Python"}
        </Button>
        <Button variant="ghost" onClick={downloadPython} disabled={!python}>
          Download .py
        </Button>
      </div>

      {examples ? (
        <div className="flex flex-wrap gap-2" aria-label="Examples">
          {examples.map((example) => (
            <button
              key={example.id}
              type="button"
              className="rounded-full border border-line px-2.5 py-1 text-xs text-muted hover:text-paper"
              onClick={() => {
                setSource(example.source);
                setTranslation(null);
                setValidation(null);
              }}
            >
              {example.id}
            </button>
          ))}
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <section>
          <h2 className="mb-2 text-sm font-medium text-muted">Q source</h2>
          <QEditor value={source} onChange={setSource} />
        </section>
        <section>
          <h2 className="mb-2 text-sm font-medium text-muted">Generated Python</h2>
          {python ? (
            <PythonEditor value={python} />
          ) : (
            <div className="flex h-[320px] items-center justify-center rounded-md border border-dashed border-line px-6 text-center text-sm text-muted">
              {translation?.support === "unsupported"
                ? "No Python was generated. See the diagnostic."
                : "Translate a supported program to see Python here."}
            </div>
          )}
        </section>
      </div>

      <section aria-live="polite" className="space-y-3">
        {busy ? <p className="text-sm text-muted">Running the pipeline…</p> : null}
        {error ? (
          <p className="rounded-md border border-bad/40 bg-bad/10 px-3 py-2 text-sm text-bad" role="alert">
            {error}
          </p>
        ) : null}
        {empty ? (
          <p className="rounded-md border border-line px-3 py-2 text-sm text-muted">
            The editor is empty. Load an example or paste a q expression such as <code>2*3+4</code>.
          </p>
        ) : null}
        {translation ? (
          <ol className="flex flex-wrap gap-2" aria-label="Pipeline status">
            {stages.map((stage) => {
              const state = translation.stages[stage] ?? "pending";
              return (
                <li key={stage} className="rounded-md border border-line px-2 py-1 text-xs">
                  <span className="text-muted">{stage}</span>{" "}
                  <span className={state === "ok" ? "text-ok" : state === "error" || state === "skipped" ? "text-warn" : "text-muted"}>
                    {state}
                  </span>
                </li>
              );
            })}
          </ol>
        ) : null}
      </section>

      {translation ? (
        <section>
          <div className="mb-3 flex flex-wrap gap-2" role="tablist" aria-label="Inspectors">
            {(
              [
                ["diagnostics", "Diagnostics"],
                ["output", "Output"],
                ["tokens", "Tokens"],
                ["ast", "AST"],
                ["ir", "IR"],
              ] as const
            ).map(([id, label]) => (
              <button
                key={id}
                type="button"
                role="tab"
                aria-selected={panel === id}
                className={`rounded-md px-2.5 py-1 text-sm ${panel === id ? "bg-white/10 text-paper" : "text-muted"}`}
                onClick={() => setPanel(id)}
              >
                {label}
              </button>
            ))}
          </div>
          {panel === "diagnostics" ? (
            translation.diagnostics.length ? (
              <ul className="space-y-2">
                {translation.diagnostics.map((item, index) => (
                  <li key={`${item.code}-${index}`} className="rounded-md border border-line px-3 py-2 text-sm">
                    <div className="flex flex-wrap items-center gap-2">
                      <SupportBadge support={item.support} />
                      <span className="font-mono text-xs text-muted">
                        {item.code} · {item.stage} · {item.line}:{item.col}
                      </span>
                    </div>
                    <p className="mt-1">{item.message}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted">No diagnostics. The pipeline accepted this program.</p>
            )
          ) : null}
          {panel === "output" ? (
            validation ? (
              <div className="space-y-3 text-sm">
                <p>
                  Comparison: <span className="font-medium">{validation.comparison}</span>
                  {validation.matched === null ? "" : validation.matched ? " · matched" : " · not matched"}
                </p>
                <p className="font-mono text-paper">{validation.display || "No display value."}</p>
                {validation.signal ? <p>Signal: {validation.signal}</p> : null}
                <JsonBlock value={{ canon: validation.canon, expected: validation.expected }} />
              </div>
            ) : (
              <p className="text-sm text-muted">
                Validate to execute the generated Python in the local sandbox. Without an authored expected value,
                the comparison is execution only.
              </p>
            )
          ) : null}
          {panel === "tokens" ? <JsonBlock value={translation.tokens} /> : null}
          {panel === "ast" ? <JsonBlock value={translation.ast} /> : null}
          {panel === "ir" ? <JsonBlock value={translation.ir} /> : null}
          {translation.features.length ? (
            <p className="mt-3 text-xs text-muted">Features: {translation.features.join(", ")}</p>
          ) : null}
          {translation.maps.length ? (
            <p className="mt-1 text-xs text-muted">Source map entries: {translation.maps.length}</p>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
