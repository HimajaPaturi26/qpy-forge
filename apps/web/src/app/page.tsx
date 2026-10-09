import Link from "next/link";

const steps = [
  "Q source",
  "Lexer",
  "Parser",
  "Semantic analysis",
  "IR",
  "Python",
  "Sandbox",
  "Authored expected value",
  "Measurement",
];

export default function HomePage() {
  return (
    <div className="space-y-10">
      <section className="max-w-3xl space-y-4">
        <p className="text-sm font-medium text-amber">q to Python workbench</p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">Translate q to Python</h1>
        <p className="text-lg leading-8 text-muted">
          Q2Py Forge translates a documented subset of q, runs the generated Python in a local sandbox, and compares
          results with expected values written into the corpus. Unsupported syntax is rejected rather than guessed.
        </p>
        <div className="flex flex-wrap gap-3">
          <Link href="/studio" className="rounded-md bg-amber px-4 py-2 text-sm font-medium text-ink">
            Open studio
          </Link>
          <Link href="/dashboard" className="rounded-md border border-line px-4 py-2 text-sm font-medium">
            View holdout agreement
          </Link>
        </div>
      </section>
      <section>
        <h2 className="text-sm font-medium text-muted">Pipeline</h2>
        <ol className="mt-3 flex flex-wrap gap-2">
          {steps.map((step, index) => (
            <li key={step} className="surface px-3 py-2 text-sm">
              <span className="text-muted">{index + 1}. </span>
              {step}
            </li>
          ))}
        </ol>
      </section>
      <section className="grid gap-4 sm:grid-cols-3">
        <article className="surface p-4">
          <h2 className="font-medium">Refusal over a guess</h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            Unsupported syntax returns a diagnostic and an empty Python program. Partial constructs stay out of the
            holdout agreement denominator.
          </p>
        </article>
        <article className="surface p-4">
          <h2 className="font-medium">Authored expectations</h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            Agreement is measured against values written into the corpus. It is not a live kdb+ confirmation. The q
            oracle is reported separately and is not required to run the studio.
          </p>
        </article>
        <article className="surface p-4">
          <h2 className="font-medium">Measured on the Accuracy page</h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            Rates on the Accuracy page come from the current corpus response. This page does not display a score.
          </p>
        </article>
      </section>
    </div>
  );
}
