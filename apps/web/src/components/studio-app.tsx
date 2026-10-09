"use client";

import { useRef, useState } from "react";
import { EditorPlaceholder, PythonEditor, QEditor } from "@/components/editors";
import { JsonBlock } from "@/components/json-block";
import { SupportBadge } from "@/components/support-badge";
import { Notice, PageHeader } from "@/components/ui/notice";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { comparisonLabel, stageLabel, stageTone } from "@/lib/format";
import { cn } from "@/lib/cn";
import type { Translation, Validation } from "@/lib/types";

type Example = { id: string; source: string; support: string };
type Panel = "diagnostics" | "output" | "tokens" | "ast" | "ir";

const stages = [
  ["lex", "Lex"],
  ["parse", "Parse"],
  ["semantic", "Semantic"],
  ["ir", "IR"],
  ["codegen", "Codegen"],
  ["compile", "Compile"],
  ["exec", "Execute"],
  ["compare", "Compare"],
] as const;

const toneClass = {
  ok: "text-ok",
  bad: "text-bad",
  warn: "text-warn",
  muted: "text-muted",
} as const;

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
  const sourceRef = useRef(source);
  const runId = useRef(0);
  sourceRef.current = source;

  function replaceSource(next: string) {
    runId.current += 1;
    setSource(next);
    setTranslation(null);
    setValidation(null);
    setError(null);
    setCopied(false);
  }

  function editSource(next: string) {
    setSource(next);
    if (translation && next !== translation.source) {
      runId.current += 1;
      setTranslation(null);
      setValidation(null);
      setCopied(false);
    }
  }

  async function loadExamples() {
    setError(null);
    try {
      const payload = await api<{ examples: Example[] }>("/api/v1/examples");
      setExamples(payload.examples);
      if (!sourceRef.current.trim() && payload.examples[0]) {
        replaceSource(payload.examples[0].source);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load examples");
    }
  }

  async function translate() {
    const sent = sourceRef.current;
    if (!sent.trim()) {
      setError("Enter q source, load an example, or upload a .q file.");
      return;
    }
    const id = ++runId.current;
    setBusy("translate");
    setError(null);
    setValidation(null);
    try {
      const result = await api<Translation>("/api/v1/translate", {
        method: "POST",
        body: JSON.stringify({ source: sent }),
      });
      if (runId.current !== id || sourceRef.current !== sent) {
        return;
      }
      setTranslation(result);
      setPanel(result.diagnostics.length ? "diagnostics" : "output");
    } catch (err) {
      if (runId.current !== id) {
        return;
      }
      setTranslation(null);
      setValidation(null);
      setError(err instanceof Error ? err.message : "Translation failed");
    } finally {
      if (runId.current === id) {
        setBusy(null);
      }
    }
  }

  async function validate() {
    const sent = sourceRef.current;
    if (!sent.trim()) {
      setError("There is no q source to validate.");
      return;
    }
    const id = ++runId.current;
    setBusy("validate");
    setError(null);
    try {
      const result = await api<Validation>("/api/v1/validate", {
        method: "POST",
        body: JSON.stringify({ source: sent }),
      });
      if (runId.current !== id || sourceRef.current !== sent) {
        return;
      }
      setTranslation(result);
      setValidation(result);
      setPanel("output");
    } catch (err) {
      if (runId.current !== id) {
        return;
      }
      setValidation(null);
      setError(err instanceof Error ? err.message : "Validation failed");
    } finally {
      if (runId.current === id) {
        setBusy(null);
      }
    }
  }

  function upload(file: File | undefined) {
    if (!file) {
      return;
    }
    const reader = new FileReader();
    reader.onload = () => replaceSource(String(reader.result ?? ""));
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
  const rejected = translation?.support === "unsupported" || translation?.stages.compile === "error";

  return (
    <div className="space-y-4">
      <PageHeader
        title="Translation studio"
        lede="Translate q source into Python and inspect compilation, execution, and validation results."
        actions={translation ? <SupportBadge support={translation.support} /> : null}
      />

      <div className="flex flex-wrap items-center gap-2">
        <Button onClick={() => void translate()} disabled={busy !== null || !source.trim()}>
          {busy === "translate" ? "Translating" : "Translate"}
        </Button>
        <Button variant="secondary" onClick={() => void validate()} disabled={busy !== null || !source.trim()}>
          {busy === "validate" ? "Validating" : "Validate"}
        </Button>
        <Button variant="outline" onClick={() => fileRef.current?.click()} disabled={busy !== null}>
          Upload .q
        </Button>
        <Button variant="outline" onClick={() => void loadExamples()} disabled={busy !== null}>
          Examples
        </Button>
        <input
          ref={fileRef}
          type="file"
          accept=".q,text/plain"
          className="sr-only"
          aria-label="Upload a q file"
          onChange={(event) => {
            upload(event.target.files?.[0]);
            event.target.value = "";
          }}
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
              className="rounded-md border border-line px-2.5 py-1 text-xs text-muted hover:text-paper"
              onClick={() => replaceSource(example.source)}
            >
              {example.id}
              <span className="sr-only">, {example.support}</span>
            </button>
          ))}
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <section>
          <h2 className="mb-2 text-sm font-medium">Q source</h2>
          <QEditor value={source} onChange={editSource} />
        </section>
        <section>
          <h2 className="mb-2 text-sm font-medium">Generated Python</h2>
          {python ? (
            <PythonEditor value={python} />
          ) : (
            <EditorPlaceholder>{rejected ? "Translation rejected" : "No generated output"}</EditorPlaceholder>
          )}
        </section>
      </div>

      <section aria-live="polite" className="space-y-3">
        {busy ? <p className="text-sm text-muted">{busy === "translate" ? "Translating" : "Validating"}</p> : null}
        {error ? <Notice tone="error">{error}</Notice> : null}
        {translation ? (
          <ol className="flex flex-wrap gap-x-4 gap-y-1 text-xs" aria-label="Pipeline status">
            {stages.map(([stage, label]) => {
              const state = translation.stages[stage];
              return (
                <li key={stage}>
                  <span className="text-muted">{label}</span>{" "}
                  <span className={toneClass[stageTone(state)]}>{stageLabel(state)}</span>
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
                ["output", "Execution"],
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
                className={cn(
                  "rounded-md px-2.5 py-1 text-sm",
                  panel === id ? "bg-white/10 text-paper" : "text-muted",
                )}
                onClick={() => setPanel(id)}
              >
                {label}
                {id === "diagnostics" && translation.diagnostics.length ? ` (${translation.diagnostics.length})` : ""}
              </button>
            ))}
          </div>
          {panel === "diagnostics" ? (
            translation.diagnostics.length ? (
              <ul className="space-y-2">
                {translation.diagnostics.map((item, index) => (
                  <li key={`${item.code}-${index}`} className="border-b border-line py-2 text-sm">
                    <div className="flex flex-wrap items-center gap-2">
                      <SupportBadge support={item.support} />
                      <span className="font-mono text-xs text-muted">
                        {item.code} · {item.stage} · {item.line}:{item.col} · {item.severity}
                      </span>
                    </div>
                    <p className="mt-1">{item.message}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted">No diagnostics</p>
            )
          ) : null}
          {panel === "output" ? (
            validation ? (
              <div className="space-y-2 text-sm">
                <p>{comparisonLabel(validation.comparison)}</p>
                <p>{validation.executed ? "Returned a value" : "No returned value"}</p>
                {validation.executed ? <p className="font-mono">{validation.display || "No display value"}</p> : null}
                {validation.signal ? <p>Signal {validation.signal}</p> : null}
                <p className="text-muted">{oracleSummaryText(validation)}</p>
                <JsonBlock value={{ canon: validation.canon, expected: validation.expected }} />
              </div>
            ) : (
              <p className="text-sm text-muted">Not run</p>
            )
          ) : null}
          {panel === "tokens" ? <JsonBlock value={translation.tokens} /> : null}
          {panel === "ast" ? <JsonBlock value={translation.ast} /> : null}
          {panel === "ir" ? <JsonBlock value={translation.ir} /> : null}
          {translation.features.length ? (
            <p className="mt-3 text-xs text-muted">Recorded features: {translation.features.join(", ")}</p>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}

function oracleSummaryText(validation: Validation): string {
  const summary = validation.oracle.available ? "q oracle not enabled" : "q oracle unavailable";
  return `${summary} — ${validation.oracle.reason}`;
}
