"use client";

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
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
  muted: "text-secondary",
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
  const [pane, setPane] = useState<"source" | "python">("source");
  const fileRef = useRef<HTMLInputElement>(null);
  const params = useSearchParams();
  const loadedQuery = useRef(false);
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

  useEffect(() => {
    if (loadedQuery.current) {
      return;
    }
    loadedQuery.current = true;
    const incoming = params.get("source");
    if (incoming) {
      replaceSource(incoming);
    }
  }, [params]);

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
  const hint = recoveryHint(error);

  return (
    <div className="space-y-5">
      <PageHeader
        title="Translation studio"
        lede="Translate q source into Python, then validate when you want the program to run."
        actions={translation ? <SupportBadge support={translation.support} /> : null}
      />

      <details className="text-sm text-secondary">
        <summary className="min-h-11 cursor-pointer py-2 text-paper">How to use Studio</summary>
        <ol className="mt-1 max-w-3xl list-decimal space-y-1 pl-5">
          <li>Load an example, upload a .q file, or type in Q source.</li>
          <li>Translate generates Python. Compile can pass while Execute stays not run.</li>
          <li>Validate executes the program. Compare stays not run without an authored expectation.</li>
          <li>Diagnostics lists refusals. Tokens, AST, and IR show the compiler stages.</li>
        </ol>
      </details>

      <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
        <div className="flex flex-wrap gap-2">
          <Button className="min-h-11 min-w-28" onClick={() => void translate()} disabled={busy !== null || !source.trim()}>
            {busy === "translate" ? "Translating" : "Translate"}
          </Button>
          <Button className="min-h-11 min-w-28" variant="secondary" onClick={() => void validate()} disabled={busy !== null || !source.trim()}>
            {busy === "validate" ? "Validating" : "Validate"}
          </Button>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button className="min-h-11" variant="outline" onClick={() => fileRef.current?.click()} disabled={busy !== null}>
            Upload .q
          </Button>
          <Button className="min-h-11" variant="outline" onClick={() => void loadExamples()} disabled={busy !== null}>
            Examples
          </Button>
          <Button className="min-h-11" variant="ghost" onClick={() => void copyPython()} disabled={!python}>
            {copied ? "Copied" : "Copy Python"}
          </Button>
          <Button className="min-h-11" variant="ghost" onClick={downloadPython} disabled={!python}>
            Download .py
          </Button>
        </div>
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
      </div>

      {examples ? (
        <div className="flex flex-wrap gap-2" aria-label="Examples">
          {examples.map((example) => (
            <button
              key={example.id}
              type="button"
              className="rounded-md border border-line px-2.5 py-1 text-xs text-secondary hover:text-paper"
              onClick={() => replaceSource(example.source)}
            >
              {example.id}
              <span className="sr-only">, {example.support}</span>
            </button>
          ))}
        </div>
      ) : null}

      <div className="flex gap-2 lg:hidden" role="tablist" aria-label="Editor">
        {(
          [
            ["source", "Q source"],
            ["python", "Generated Python"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            id={`editor-tab-${id}`}
            type="button"
            role="tab"
            aria-selected={pane === id}
            aria-controls={`editor-panel-${id}`}
            className={cn(
              "min-h-11 flex-1 rounded-md border px-3 text-sm",
              pane === id ? "border-accent bg-accent/10 text-paper" : "border-line text-secondary",
            )}
            onClick={() => setPane(id)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="grid min-w-0 items-start gap-4 lg:grid-cols-2">
        <section
          id="editor-panel-source"
          role="tabpanel"
          aria-labelledby="editor-tab-source"
          className={cn("min-w-0", pane !== "source" && "hidden lg:block")}
        >
          <h2 className="mb-2 text-sm font-medium">Q source</h2>
          <QEditor value={source} onChange={editSource} />
        </section>
        <section
          id="editor-panel-python"
          role="tabpanel"
          aria-labelledby="editor-tab-python"
          className={cn("min-w-0", pane !== "python" && "hidden lg:block")}
        >
          <h2 className="mb-2 text-sm font-medium">Generated Python</h2>
          {python ? (
            <PythonEditor value={python} />
          ) : (
            <EditorPlaceholder>
              {rejected ? "Translation stopped before Python was emitted" : "Translate to generate Python"}
            </EditorPlaceholder>
          )}
        </section>
      </div>

      <section aria-live="polite" className="space-y-3">
        {busy ? <p className="text-sm text-secondary">{busy === "translate" ? "Translating" : "Validating"}</p> : null}
        {error ? <Notice tone="error">{error}</Notice> : null}
        {hint ? <p className="text-sm text-secondary">{hint}</p> : null}
        <ol className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-4 lg:grid-cols-8" aria-label="Pipeline status">
          {stages.map(([stage, label]) => {
            const state = translation?.stages[stage];
            const tone = stageTone(state);
            return (
              <li key={stage} className="min-w-0 rounded-md border border-accent/30 bg-elevated px-2 py-2">
                <span className="block font-medium text-accent">{label}</span>
                <span className={cn("mt-0.5 block break-words", toneClass[tone])}>{stageLabel(state)}</span>
              </li>
            );
          })}
        </ol>
        <p className="text-xs leading-5 text-secondary">
          Translate reports Lex through Compile. Validate runs Execute. Compare stays not run without an authored
          expectation.
        </p>
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
                  "min-h-11 rounded-md px-3 text-sm",
                  panel === id ? "bg-accent/15 text-paper" : "text-secondary",
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
                      <span className="font-mono text-xs text-secondary">
                        {item.code} · {item.stage} · {item.line}:{item.col} · {item.severity}
                      </span>
                    </div>
                    <p className="mt-1 break-words">{item.message}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-secondary">No diagnostics</p>
            )
          ) : null}
          {panel === "output" ? (
            validation ? (
              <div className="space-y-3 text-sm">
                <dl className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <dt className="text-xs text-secondary">Comparison</dt>
                    <dd className="mt-1 break-words">{comparisonLabel(validation.comparison)}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-secondary">Execution</dt>
                    <dd className="mt-1">{validation.executed ? "Returned a value" : "No returned value"}</dd>
                  </div>
                  {validation.executed ? (
                    <div className="sm:col-span-2">
                      <dt className="text-xs text-secondary">Display</dt>
                      <dd className="mt-1 break-all font-mono">{validation.display || "No display value"}</dd>
                    </div>
                  ) : null}
                  {validation.signal ? (
                    <div>
                      <dt className="text-xs text-secondary">Signal</dt>
                      <dd className="mt-1 break-words">{validation.signal}</dd>
                    </div>
                  ) : null}
                  <div className="sm:col-span-2">
                    <dt className="text-xs text-secondary">q oracle</dt>
                    <dd className="mt-1 break-words text-secondary">{oracleSummaryText(validation)}</dd>
                  </div>
                </dl>
                <JsonBlock value={{ canon: validation.canon, expected: validation.expected }} />
              </div>
            ) : (
              <p className="text-sm text-secondary">
                Not run. Translate does not execute the program. Use Validate to run it.
              </p>
            )
          ) : null}
          {panel === "tokens" ? <JsonBlock value={translation.tokens} /> : null}
          {panel === "ast" ? <JsonBlock value={translation.ast} /> : null}
          {panel === "ir" ? <JsonBlock value={translation.ir} /> : null}
          {translation.features.length ? (
            <p className="mt-3 text-xs text-secondary">Recorded features: {translation.features.join(", ")}</p>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}

function recoveryHint(error: string | null): string | null {
  if (!error) {
    return null;
  }
  if (error.startsWith("Enter") || error.startsWith("There is no") || error.startsWith("Could not read")) {
    return null;
  }
  return "Correct the source and translate again. If the service did not respond, open Status and confirm the API is reachable.";
}

function oracleSummaryText(validation: Validation): string {
  const summary = validation.oracle.available ? "q oracle not enabled" : "q oracle unavailable";
  return `${summary}: ${validation.oracle.reason}`;
}
