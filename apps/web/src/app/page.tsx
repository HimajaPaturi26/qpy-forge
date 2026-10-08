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
  "Metrics",
];

export default function HomePage() {
  return (
    <div className="space-y-10">
      <section className="max-w-3xl space-y-4">
        <p className="text-sm font-medium uppercase tracking-wide text-amber">Open-source q subset translator</p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">Translate q you can defend.</h1>
        <p className="text-lg text-muted">
          Q2Py Studio turns a documented subset of q into Python, runs that Python in a local sandbox, and compares
          the result with expected values written by hand. If a construct is not in scope, the translator refuses it.
        </p>
        <div className="flex flex-wrap gap-3">
          <Link href="/studio" className="rounded-md bg-amber px-4 py-2 text-sm font-medium text-ink">
            Open the studio
          </Link>
          <Link href="/dashboard" className="rounded-md border border-line px-4 py-2 text-sm font-medium">
            Measured accuracy
          </Link>
        </div>
      </section>
      <section>
        <h2 className="text-sm font-medium text-muted">Pipeline</h2>
        <ol className="mt-3 flex flex-wrap gap-2">
          {steps.map((step, index) => (
            <li key={step} className="rounded-md border border-line px-3 py-2 text-sm">
              <span className="mr-2 text-muted">{index + 1}</span>
              {step}
            </li>
          ))}
        </ol>
      </section>
      <section className="grid gap-4 sm:grid-cols-3">
        <article className="rounded-lg border border-line p-4">
          <h2 className="font-medium">Refusal over a guess</h2>
          <p className="mt-2 text-sm text-muted">
            Unsupported syntax returns a diagnostic and an empty Python program. Partial constructs are labeled and
            kept out of the headline accuracy denominator.
          </p>
        </article>
        <article className="rounded-lg border border-line p-4">
          <h2 className="font-medium">No q license required</h2>
          <p className="mt-2 text-sm text-muted">
            Development, tests, and the studio run without kdb+. When the q binary is absent, the status line is
            Oracle: unavailable.
          </p>
        </article>
        <article className="rounded-lg border border-line p-4">
          <h2 className="font-medium">Numbers from the corpus</h2>
          <p className="mt-2 text-sm text-muted">
            The dashboard reads the latest holdout measurement. It does not display a target as if it were a result.
          </p>
        </article>
      </section>
    </div>
  );
}
