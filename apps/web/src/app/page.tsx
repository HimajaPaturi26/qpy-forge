import Link from "next/link";
import { HomeStatus } from "@/components/home-status";

const translationStages = [
  "Q source",
  "Lexer",
  "Parser",
  "Semantic analysis",
  "IR",
  "Python generation",
  "Compilation",
];

const optionalStages = ["Execution", "Validation"];

const capabilities = [
  {
    title: "Translation",
    body: "Translate the supported q subset into inspectable Python. Unsupported syntax is rejected rather than guessed.",
  },
  {
    title: "Validation",
    body: "Compare execution results against independently authored expected values. Live q-oracle comparison is a separate capability.",
  },
  {
    title: "Diagnostics",
    body: "Inspect stage-level failures and identify where translation stops.",
  },
];

const snapshot = [
  { href: "/studio", label: "Compiler pipeline", detail: "Lex through compile, then optional execution" },
  { href: "/docs", label: "Supported syntax and refusal", detail: "In-scope subset and constructs that return no Python" },
  { href: "/validate", label: "Authored-value validation", detail: "Corpus expectations, not a live q process" },
  { href: "/dashboard", label: "Corpus and holdout reporting", detail: "Supported holdout agreement and the construct registry" },
  { href: "/settings", label: "Execution constraints", detail: "Sandbox boundary, resource limits, and durability" },
];

export default function HomePage() {
  return (
    <div className="space-y-16">
      <section className="max-w-3xl space-y-6 pt-4">
        <p className="text-sm text-amber">Q2Py Forge</p>
        <h1 className="max-w-2xl text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">
          Translate q. Validate the result. Understand the limits.
        </h1>
        <p className="max-w-2xl text-base leading-7 text-muted">
          An engineering workbench for translating supported Q/kdb+ expressions into Python, inspecting the compiler
          pipeline, and validating results against authored expectations.
        </p>
        <div className="flex flex-wrap gap-3">
          <Link href="/studio" className="rounded-md bg-amber px-4 py-2 text-sm font-medium text-ink">
            Open translation studio
          </Link>
          <Link href="/validate" className="rounded-md border border-line px-4 py-2 text-sm font-medium">
            Explore validation
          </Link>
        </div>
      </section>

      <section aria-labelledby="pipeline-heading">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 id="pipeline-heading" className="text-sm font-medium">
            Pipeline
          </h2>
          <p className="text-xs text-muted">Stages are reported per translation. Later stages do not run after a refusal.</p>
        </div>
        <ol className="mt-4 flex flex-wrap items-center gap-2">
          {translationStages.map((stage, index) => (
            <li key={stage} className="flex items-center gap-2">
              <span className="border border-line px-2.5 py-1.5 text-sm">{stage}</span>
              {index < translationStages.length - 1 ? (
                <span aria-hidden="true" className="text-muted">
                  →
                </span>
              ) : null}
            </li>
          ))}
          <li className="flex items-center gap-2">
            <span aria-hidden="true" className="text-muted">
              →
            </span>
            <span className="border border-dashed border-line px-2.5 py-1.5 text-sm text-muted">
              Optional execution and validation
            </span>
          </li>
        </ol>
        <p className="sr-only">
          Translation stages are {translationStages.join(", ")}. Optional stages are {optionalStages.join(" and ")}.
        </p>
      </section>

      <section aria-labelledby="capabilities-heading">
        <h2 id="capabilities-heading" className="text-sm font-medium">
          Capabilities
        </h2>
        <div className="mt-4 grid gap-8 border-t border-line pt-4 md:grid-cols-3">
          {capabilities.map((item) => (
            <article key={item.title}>
              <h3 className="text-base font-medium">{item.title}</h3>
              <p className="mt-2 text-sm leading-6 text-muted">{item.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section aria-labelledby="inspect-heading">
        <h2 id="inspect-heading" className="text-sm font-medium">
          What you can inspect
        </h2>
        <ul className="mt-4 divide-y divide-line border-y border-line">
          {snapshot.map((item) => (
            <li key={item.href}>
              <Link href={item.href} className="grid gap-1 py-3 sm:grid-cols-[16rem_1fr] sm:gap-6">
                <span className="text-sm font-medium">{item.label}</span>
                <span className="text-sm text-muted">{item.detail}</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="limits-heading">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 id="limits-heading" className="text-sm font-medium">
            Limits
          </h2>
          <Link href="/settings" className="text-sm text-muted underline decoration-line underline-offset-4">
            Open status
          </Link>
        </div>
        <div className="mt-4">
          <HomeStatus />
        </div>
      </section>

      <section aria-labelledby="creator-heading" className="max-w-2xl border-t border-line pt-8">
        <h2 id="creator-heading" className="text-lg font-medium">
          Built by Himaja Paturi
        </h2>
        <p className="mt-2 text-sm leading-6 text-muted">
          An independent engineering project exploring Q/kdb+ to Python translation, compiler architecture, and
          validation of generated code.
        </p>
        <a
          href="https://www.linkedin.com/in/himajapaturi/"
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-block text-sm text-amber underline decoration-amber/40 underline-offset-4"
        >
          View professional profile
        </a>
      </section>
    </div>
  );
}
