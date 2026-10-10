import Link from "next/link";

const exampleSource = "2*3+4";
const exampleExpression = "q.mul(q.long(2), q.add(q.long(3), q.long(4)))";
const examplePython = `import q2py.runtime as q

def q2py_program():
    env = q.Env()
    _v1 = ${exampleExpression}
    return _v1
`;

const studioExample = `/studio?source=${encodeURIComponent(exampleSource)}`;

const steps = [
  {
    title: "Write or load Q",
    body: "Type a supported expression, open the example, or upload a .q file.",
  },
  {
    title: "Inspect the translation",
    body: "Read the generated Python and the outcome of each compiler stage.",
  },
  {
    title: "Validate the result",
    body: "Run the program and compare it with an authored expectation when one exists.",
  },
];

const benefits = [
  {
    title: "Each stage is visible",
    body: "Lex, parse, semantic analysis, IR, codegen, and compile report their own outcome.",
  },
  {
    title: "Python you can read",
    body: "Supported translations can be copied or downloaded from Studio.",
  },
  {
    title: "Checks you can trace",
    body: "Validate compares a corpus case with the value or signal written on that record.",
  },
  {
    title: "Limits stay explicit",
    body: "Unsupported syntax stops with a diagnostic. Skipped stages stay marked not run.",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-16 sm:space-y-20">
      <section className="grid items-center gap-8 pt-4 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:gap-12 lg:pt-8">
        <div className="max-w-xl space-y-5">
          <p className="text-sm font-medium text-amber">Q2Py Forge</p>
          <h1 className="text-4xl font-bold leading-[1.12] tracking-tight sm:text-5xl">
            From q to Python. See every step.
          </h1>
          <p className="text-base leading-7 text-secondary">
            Translate supported Q/kdb+ expressions into Python, inspect the compiler pipeline, and validate results
            against authored expectations.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <Link
              href="/studio"
              className="inline-flex min-h-11 items-center justify-center rounded-md bg-amber px-4 text-sm font-semibold text-ink hover:bg-amber-hover"
            >
              Open Studio
            </Link>
            <Link
              href={studioExample}
              className="inline-flex min-h-11 items-center justify-center rounded-md border border-line px-4 text-sm font-semibold hover:border-accent hover:bg-white/5"
            >
              Try an example
            </Link>
          </div>
        </div>
        <ProductPreview />
      </section>

      <section aria-labelledby="workflow-heading">
        <h2 id="workflow-heading" className="text-lg font-semibold">
          How it works
        </h2>
        <ol className="mt-5 grid gap-4 sm:grid-cols-3">
          {steps.map((step, index) => (
            <li key={step.title} className="surface p-4">
              <p className="text-xs font-semibold text-accent">Step {index + 1}</p>
              <h3 className="mt-2 text-sm font-medium">{step.title}</h3>
              <p className="mt-2 text-sm leading-6 text-secondary">{step.body}</p>
            </li>
          ))}
        </ol>
      </section>

      <section aria-labelledby="benefits-heading">
        <h2 id="benefits-heading" className="text-lg font-semibold">
          What you get
        </h2>
        <ul className="mt-5 grid gap-x-8 gap-y-6 sm:grid-cols-2">
          {benefits.map((item) => (
            <li key={item.title} className="border-t border-line pt-4">
              <h3 className="text-sm font-medium">{item.title}</h3>
              <p className="mt-2 text-sm leading-6 text-secondary">{item.body}</p>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="example-heading">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div className="max-w-2xl">
            <h2 id="example-heading" className="text-lg font-semibold">
              A supported example
            </h2>
            <p className="mt-2 text-sm leading-6 text-secondary">
              Q has no operator precedence, so <code>2*3+4</code> is <code>2*(3+4)</code>. This is the Python the
              current translator emits. It is not an execution result and not a live q check.
            </p>
          </div>
          <Link
            href={studioExample}
            className="inline-flex min-h-11 items-center text-sm font-medium text-accent underline decoration-accent/40 underline-offset-4 hover:text-accent-hover"
          >
            Open in Studio
          </Link>
        </div>
        <div className="mt-5 grid min-w-0 gap-4 lg:grid-cols-2">
          <CodeSample label="Q source" code={exampleSource} />
          <CodeSample label="Generated Python" code={examplePython} />
        </div>
      </section>

      <section aria-labelledby="credibility-heading" className="grid gap-8 border-t border-line pt-8 lg:grid-cols-2">
        <div>
          <h2 id="credibility-heading" className="text-lg font-semibold">
            Measured against authored expectations
          </h2>
          <p className="mt-2 text-sm leading-6 text-secondary">
            Holdout agreement is a comparison with values and signals written for this corpus. Docs describe the
            supported subset, the sandbox boundary, and what this build does not claim.
          </p>
          <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-sm">
            <Link href="/docs" className="inline-flex min-h-11 items-center font-medium text-accent underline decoration-accent/40 underline-offset-4 hover:text-accent-hover">
              Documentation
            </Link>
            <Link href="/dashboard" className="inline-flex min-h-11 items-center text-secondary underline decoration-line underline-offset-4">
              Accuracy
            </Link>
            <Link href="/settings" className="inline-flex min-h-11 items-center text-secondary underline decoration-line underline-offset-4">
              Status
            </Link>
          </div>
        </div>
        <div>
          <h2 className="text-lg font-semibold">Built by Himaja Paturi</h2>
          <p className="mt-2 text-sm leading-6 text-secondary">
            An independent engineering project for Q/kdb+ to Python translation, compiler inspection, and systematic
            checks of generated code.
          </p>
          <a
            href="https://www.linkedin.com/in/himajapaturi/"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 inline-flex min-h-11 items-center text-sm font-medium text-accent underline decoration-accent/40 underline-offset-4 hover:text-accent-hover"
          >
            Connect on LinkedIn
          </a>
        </div>
      </section>
    </div>
  );
}

function ProductPreview() {
  const stages = ["Lex", "Parse", "Semantic", "IR", "Codegen", "Compile"];
  return (
    <div className="surface min-w-0 p-4 sm:p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-secondary">Translator preview</p>
      <p className="mt-4 font-mono text-lg text-paper">{exampleSource}</p>
      <p className="mt-2 break-all font-mono text-xs leading-5 text-secondary">{exampleExpression}</p>
      <ol className="mt-4 flex flex-wrap gap-2" aria-label="Compiler stages reported after Translate">
        {stages.map((stage) => (
          <li key={stage} className="rounded-md border border-accent/40 px-2 py-1 text-xs font-medium text-accent">
            {stage}
          </li>
        ))}
      </ol>
      <p className="mt-4 text-xs leading-5 text-secondary">Execute and Compare stay not run until Validate.</p>
    </div>
  );
}

function CodeSample({ label, code }: { label: string; code: string }) {
  return (
    <figure className="min-w-0">
      <figcaption className="mb-1 text-xs text-secondary">{label}</figcaption>
      <pre className="max-h-56 overflow-auto rounded-md border border-line bg-ink p-3 font-mono text-xs leading-5 text-paper">
        {code}
      </pre>
    </figure>
  );
}
