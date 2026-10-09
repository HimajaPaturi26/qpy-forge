import Link from "next/link";

const exampleSource = "2*3+4";
const examplePython = `import q2py.runtime as q

def q2py_program():
    env = q.Env()
    _v1 = q.mul(q.long(2), q.add(q.long(3), q.long(4)))
    return _v1
`;

const studioExample = `/studio?source=${encodeURIComponent(exampleSource)}`;

const steps = [
  {
    title: "Write or load Q code",
    body: "Start with a supported example or provide a source file.",
  },
  {
    title: "Inspect the translation",
    body: "Explore generated Python and the compiler's intermediate stages.",
  },
  {
    title: "Validate the result",
    body: "Review available comparisons, execution outcomes, and diagnostics.",
  },
];

const features = [
  {
    title: "Inspectable compiler pipeline",
    body: "Lexing, parsing, semantic analysis, intermediate representation, and code generation each report their own outcome.",
    href: "/docs",
    label: "Read the pipeline notes",
  },
  {
    title: "Generated Python",
    body: "Supported translations produce Python you can read, copy, and download.",
    href: "/studio",
    label: "Open Studio",
  },
  {
    title: "Validation and comparison",
    body: "Validate compares a corpus case with the authored value or signal on that record.",
    href: "/validate",
    label: "Open validation",
  },
  {
    title: "Actionable diagnostics",
    body: "Unsupported syntax stops with a diagnostic. Skipped stages stay marked as not run.",
    href: "/studio",
    label: "Inspect diagnostics in Studio",
  },
  {
    title: "Corpus and accuracy analysis",
    body: "Accuracy reports agreement with the hand-authored holdout. The corpus browser shows the cases behind that measurement.",
    href: "/dashboard",
    label: "Open accuracy",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-16 sm:space-y-20">
      <section className="grid items-start gap-10 pt-2 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="max-w-xl space-y-5">
          <p className="text-sm font-medium text-amber">Q2Py Forge</p>
          <h1 className="text-4xl font-semibold leading-[1.12] tracking-tight sm:text-5xl">
            From q to Python. See every step.
          </h1>
          <p className="text-base leading-7 text-muted">
            Translate supported Q/kdb+ expressions into Python, inspect the compiler pipeline, and validate results
            against authored expectations. Explore the generated code and diagnostics instead of treating translation as
            a black box.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
            <Link
              href="/studio"
              className="inline-flex min-h-11 items-center justify-center rounded-md bg-amber px-4 text-sm font-medium text-ink hover:bg-amber/90"
            >
              Open Studio
            </Link>
            <Link
              href={studioExample}
              className="inline-flex min-h-11 items-center justify-center rounded-md border border-line px-4 text-sm font-medium hover:bg-white/5"
            >
              Explore an example
            </Link>
          </div>
        </div>
        <PipelinePreview />
      </section>

      <section aria-labelledby="workflow-heading">
        <h2 id="workflow-heading" className="text-lg font-medium">
          How it works
        </h2>
        <ol className="mt-6 grid gap-6 sm:grid-cols-3">
          {steps.map((step, index) => (
            <li key={step.title} className="border-t border-line pt-4">
              <p className="text-xs text-amber">Step {index + 1}</p>
              <h3 className="mt-1 text-sm font-medium">{step.title}</h3>
              <p className="mt-2 text-sm leading-6 text-muted">{step.body}</p>
            </li>
          ))}
        </ol>
      </section>

      <section aria-labelledby="features-heading">
        <h2 id="features-heading" className="text-lg font-medium">
          What you can inspect
        </h2>
        <div className="mt-6 grid gap-8 sm:grid-cols-2">
          {features.map((item) => (
            <article key={item.title} className="border-t border-line pt-4">
              <h3 className="text-sm font-medium">{item.title}</h3>
              <p className="mt-2 text-sm leading-6 text-muted">{item.body}</p>
              <Link href={item.href} className="mt-3 inline-flex min-h-11 items-center text-sm text-amber underline decoration-amber/40 underline-offset-4">
                {item.label}
              </Link>
            </article>
          ))}
          <article className="border-t border-line pt-4">
            <h3 className="text-sm font-medium">Corpus browser</h3>
            <p className="mt-2 text-sm leading-6 text-muted">
              Holdout, dev, and coverage splits stay separate. The holdout rate is not a measurement of arbitrary q.
            </p>
            <Link href="/corpus" className="mt-3 inline-flex min-h-11 items-center text-sm text-amber underline decoration-amber/40 underline-offset-4">
              Browse the corpus
            </Link>
          </article>
        </div>
      </section>

      <section aria-labelledby="example-heading">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 id="example-heading" className="text-lg font-medium">
              A supported example
            </h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
              Right to left, with no operator precedence, <code>2*3+4</code> is <code>2*(3+4)</code>. This is the Python
              the current translator emits. It is not an execution result and not a live q check.
            </p>
          </div>
          <Link href={studioExample} className="text-sm text-amber underline decoration-amber/40 underline-offset-4">
            Open this example in Studio
          </Link>
        </div>
        <div className="mt-5 grid min-w-0 gap-4 lg:grid-cols-2">
          <CodeSample label="Q source" code={exampleSource} />
          <CodeSample label="Generated Python" code={examplePython} />
        </div>
      </section>

      <section aria-labelledby="credibility-heading" className="max-w-2xl border-t border-line pt-8">
        <h2 id="credibility-heading" className="text-lg font-medium">
          Architecture and validation
        </h2>
        <p className="mt-2 text-sm leading-6 text-muted">
          Translation and execution are separate stages. Accuracy on the holdout is agreement with authored expectations.
          Docs describe the supported subset, the sandbox boundary, and what this build does not claim.
        </p>
        <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-sm">
          <Link href="/docs" className="text-amber underline decoration-amber/40 underline-offset-4">
            Explore documentation
          </Link>
          <Link href="/settings" className="text-muted underline decoration-line underline-offset-4">
            Open status
          </Link>
        </div>
      </section>

      <section aria-labelledby="creator-heading" className="flex max-w-3xl flex-wrap items-end justify-between gap-4 border-t border-line pt-8">
        <div className="max-w-xl">
          <h2 id="creator-heading" className="text-lg font-medium">
            Built by Himaja Paturi
          </h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            An independent engineering project focused on Q/kdb+ to Python translation, compiler architecture, and
            systematic validation of generated code.
          </p>
        </div>
        <a
          href="https://www.linkedin.com/in/himajapaturi/"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex min-h-11 items-center text-sm text-amber underline decoration-amber/40 underline-offset-4"
        >
          Connect on LinkedIn
        </a>
      </section>
    </div>
  );
}

function PipelinePreview() {
  const stages = ["Lex", "Parse", "Semantic", "IR", "Codegen", "Compile"];
  return (
    <div className="surface min-w-0 p-4">
      <p className="text-xs text-muted">Pipeline stages reported after Translate</p>
      <ol className="mt-3 flex flex-wrap gap-2" aria-label="Compiler stages">
        {stages.map((stage) => (
          <li key={stage} className="rounded-md border border-line px-2 py-1 text-xs">
            {stage}
          </li>
        ))}
      </ol>
      <p className="mt-4 text-xs text-muted">Execution and comparison stay not run until Validate.</p>
      <div className="mt-4 grid min-w-0 gap-3">
        <CodeSample label="Q source" code={exampleSource} />
        <CodeSample label="Generated Python" code={examplePython} />
      </div>
    </div>
  );
}

function CodeSample({ label, code }: { label: string; code: string }) {
  return (
    <figure className="min-w-0">
      <figcaption className="mb-1 text-xs text-muted">{label}</figcaption>
      <pre className="max-h-48 overflow-auto rounded-md border border-line bg-ink p-3 font-mono text-xs leading-5">
        {code}
      </pre>
    </figure>
  );
}
