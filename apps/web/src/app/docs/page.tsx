const sections = [
  {
    title: "Pipeline",
    body: "q is lexed, parsed, checked, lowered to an intermediate representation, and emitted as Python when the construct is in scope. Unsupported syntax produces a diagnostic instead of generated Python.",
  },
  {
    title: "Supported subset",
    body: "Long and float arithmetic, greater (|) and lesser (&), numeric $ cast, cross, infix xexp as exp(y * log x), booleans including 01b, chars, symbols, dates and months, nulls and infinities, lists, dictionaries, simple tables, assignment, lambdas without nested closures, projections, conditionals, each, over, scan, reductions such as prd, med, and var, and a limited select, exec, update, and delete. The Accuracy registry is the list for this process. xexp is covered by regression tests and is outside the original holdout.",
  },
  {
    title: "Refused",
    body: "Dot amend, peach, if, do, while, system, read0, hopen, eval, load, save, atom roll and deal, and unrecognized syntax. A numeric cast of a symbol, or of text parsed as a number, signals type at runtime.",
  },
  {
    title: "Partial",
    body: "Short, int, byte, real, and timestamp literals are represented. The rest of the promotion grid and timestamp arithmetic are not claimed. Unary over stops at a fixed point within 1000 steps or raises limit. Partial cases are outside the holdout denominator.",
  },
  {
    title: "Validation",
    body: "Corpus expectations are authored in the corpus file. Scoring rejects provenance that starts with generated-by-translator. Validate compares a case with that record. Studio validation does not attach an expectation. Neither path calls a live q process in this build.",
  },
  {
    title: "Execution",
    body: "HTTP validation uses a Python subprocess, a stripped environment, CPU, address-space, and file-size limits, and an AST allow-list. Generated code may call only the runtime facade. Corpus scoring uses the same allow-list in-process and does not apply those resource limits. The subprocess is not a container, a VM, or a network namespace.",
  },
  {
    title: "Oracle",
    body: "With no q binary on PATH and no Q2PY_Q_BIN, the oracle is unavailable. A detected binary does not enable live oracle execution. Comparisons stay on authored values.",
  },
  {
    title: "Persistence",
    body: "History and measurement snapshots are SQLite rows in the API process. Status reports durability. Without a volume, that file is replaced with the instance.",
  },
];

export default function DocsPage() {
  return (
    <div className="max-w-3xl">
      <h1 className="text-xl font-semibold tracking-tight">Docs</h1>
      <p className="mt-1 text-sm text-muted">Behavior of this build. Not complete q coverage and not kdb+ equivalence.</p>
      <div className="mt-6 divide-y divide-line border-y border-line">
        {sections.map((section) => (
          <section key={section.title} className="grid gap-1 py-4 sm:grid-cols-[9rem_1fr] sm:gap-6">
            <h2 className="text-sm font-medium">{section.title}</h2>
            <p className="text-sm leading-6 text-muted">{section.body}</p>
          </section>
        ))}
      </div>
    </div>
  );
}
