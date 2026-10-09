import Link from "next/link";

const translationStages = [
  "Q source",
  "Lexing",
  "Parsing",
  "Semantic analysis",
  "Intermediate representation",
  "Python generation",
  "Compilation",
];

const capabilities = [
  {
    title: "Compiler pipeline",
    body: "Trace q source through lexing, parsing, semantic analysis, intermediate representation, and Python code generation.",
  },
  {
    title: "Code generation",
    body: "Inspect the Python produced by each supported translation.",
  },
  {
    title: "Result validation",
    body: "Compare execution results against independently authored expectations and investigate mismatches.",
  },
  {
    title: "Diagnostics and control",
    body: "Identify unsupported syntax, inspect stage-level failures, and understand where translation stops.",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-20">
      <section className="max-w-3xl space-y-6 pt-6">
        <p className="text-sm font-medium text-amber">Q2Py Forge</p>
        <h1 className="text-4xl font-semibold leading-[1.12] tracking-tight sm:text-5xl">
          From q to Python, with confidence at every stage
        </h1>
        <p className="max-w-2xl text-base leading-7 text-muted">
          Translate supported Q/kdb+ expressions into Python through an inspectable compiler pipeline. Examine generated
          code, validate results against authored expectations, and trace failures through clear diagnostics.
        </p>
        <div className="flex flex-wrap gap-3 pt-1">
          <Link
            href="/studio"
            className="rounded-md bg-amber px-4 py-2.5 text-sm font-medium text-ink hover:bg-amber/90"
          >
            Open translation studio
          </Link>
          <Link
            href="/validate"
            className="rounded-md border border-line px-4 py-2.5 text-sm font-medium hover:bg-white/5"
          >
            Explore validation
          </Link>
        </div>
      </section>

      <section aria-labelledby="capabilities-heading">
        <h2 id="capabilities-heading" className="text-lg font-medium">
          Engineering, made inspectable
        </h2>
        <div className="mt-6 grid gap-x-10 gap-y-8 border-t border-line pt-6 sm:grid-cols-2">
          {capabilities.map((item) => (
            <article key={item.title}>
              <h3 className="text-sm font-medium">{item.title}</h3>
              <p className="mt-2 max-w-md text-sm leading-6 text-muted">{item.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section aria-labelledby="pipeline-heading">
        <h2 id="pipeline-heading" className="text-lg font-medium">
          From source to verified results
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
          Each stage reports its actual outcome. Execution and validation run separately from translation.
        </p>
        <ol className="mt-6 flex flex-wrap items-center gap-x-2 gap-y-3">
          {translationStages.map((stage, index) => (
            <li key={stage} className="flex items-center gap-2">
              <span className="border border-line bg-panel px-2.5 py-1.5 text-sm">{stage}</span>
              {index < translationStages.length - 1 ? (
                <span aria-hidden="true" className="text-muted">
                  →
                </span>
              ) : null}
            </li>
          ))}
        </ol>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <span className="text-xs text-muted">Separate from translation</span>
          <span className="border border-dashed border-line px-2.5 py-1.5 text-sm">Execution and validation</span>
        </div>
      </section>

      <section aria-labelledby="transparency-heading" className="max-w-2xl border-t border-line pt-10">
        <h2 id="transparency-heading" className="text-lg font-medium">
          Technical transparency
        </h2>
        <p className="mt-2 text-sm leading-6 text-muted">
          Explore the supported syntax, validation methodology, runtime availability, persistence model, and execution
          constraints in the project documentation and Status page.
        </p>
        <div className="mt-4 flex flex-wrap gap-4 text-sm">
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
          className="text-sm text-amber underline decoration-amber/40 underline-offset-4"
        >
          Connect on LinkedIn
        </a>
      </section>
    </div>
  );
}
