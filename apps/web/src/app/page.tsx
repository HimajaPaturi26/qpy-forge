import Link from "next/link";

export default function HomePage() {
  return (
    <div className="max-w-3xl space-y-8">
      <section className="space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">Q2Py Forge</h1>
        <p className="text-sm leading-6 text-muted">
          q to Python translation, sandbox execution, and comparison against authored expected values. Unsupported
          syntax is rejected.
        </p>
        <div className="flex flex-wrap gap-2">
          <Link href="/studio" className="rounded-md bg-amber px-3 py-2 text-sm font-medium text-ink">
            Translation studio
          </Link>
          <Link href="/dashboard" className="rounded-md border border-line px-3 py-2 text-sm font-medium">
            Accuracy
          </Link>
        </div>
      </section>
      <p className="text-sm text-muted">
        Lex, parse, semantic analysis, IR, Python, sandbox, authored expectation
      </p>
      <dl className="max-w-xl text-sm">
        <div className="grid gap-1 border-t border-line py-3 sm:grid-cols-[9rem_1fr]">
          <dt className="text-muted">Refusal</dt>
          <dd>Out-of-scope syntax returns a diagnostic and no Python</dd>
        </div>
        <div className="grid gap-1 border-t border-line py-3 sm:grid-cols-[9rem_1fr]">
          <dt className="text-muted">Agreement</dt>
          <dd>Holdout agreement uses hand-authored expectations, not a live q process</dd>
        </div>
        <div className="grid gap-1 border-t border-b border-line py-3 sm:grid-cols-[9rem_1fr]">
          <dt className="text-muted">Oracle</dt>
          <dd>Reported on Status. Not required to translate or validate</dd>
        </div>
      </dl>
    </div>
  );
}
