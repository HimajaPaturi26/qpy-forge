const sections = [
  {
    title: "What this workbench does",
    body: "Q source is lexed, parsed, checked, lowered to an intermediate form, and, when the construct is in scope, emitted as Python. Studio validation runs that Python. Corpus validation compares the run with an expected value or signal stored on the case. Unsupported syntax produces a diagnostic and no Python.",
  },
  {
    title: "Supported syntax",
    body: "The implemented subset includes long and float arithmetic, greater (|) and lesser (&), numeric $ cast, cross, booleans including 01b vectors, chars, symbols, dates and months, nulls and infinities, lists, dictionaries, simple tables, assignment, lambdas without nested closures, projections, conditionals, the each family, over and scan, reductions such as prd, med, and var, and a small select, exec, update, and delete subset. The registry on the Accuracy page is the live list for this process.",
  },
  {
    title: "Refusals",
    body: "Dot amend, peach, if, do, while, system, read0, hopen, eval, load, save, atom roll and deal, and syntax the parser does not recognize are refused. A refusal leaves the Python field empty. A numeric cast of a symbol, or of text parsed as a number, signals type at runtime rather than guessing a value.",
  },
  {
    title: "Partial constructs",
    body: "Short, int, byte, real, and timestamp literals are represented. The rest of the promotion grid, and timestamp arithmetic, are not claimed. Unary over returns a fixed point within 1000 steps or raises limit. Partial cases are excluded from the holdout agreement denominator.",
  },
  {
    title: "Expected values",
    body: "Corpus expectations are authored in the corpus file. Scoring rejects a provenance that starts with generated-by-translator. Agreement with those values is not confirmation by a q process. The Validate page uses the expectation stored on the selected case. Studio validation does not attach one.",
  },
  {
    title: "Execution boundary",
    body: "Studio and HTTP validation use a Python subprocess with a stripped environment, CPU, address-space, and file-size limits, and an AST allow-list. Generated code may only call the runtime facade. Corpus scoring uses the same allow-list in-process and does not apply those resource limits. The subprocess is not a container, a VM, or a separate network namespace. Status reports the limits returned by the API.",
  },
  {
    title: "Oracle",
    body: "If q is not on PATH and Q2PY_Q_BIN is unset, status says the q oracle is unavailable. Finding a q binary does not enable live oracle execution in this build. Comparisons stay on authored values.",
  },
  {
    title: "History",
    body: "Translations, validations, and measurement snapshots are SQLite rows in the API process. Status reports whether that store is durable. On a serverless host without a volume, the file can disappear when the instance is replaced.",
  },
];

export default function DocsPage() {
  return (
    <div className="max-w-3xl space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Docs</h1>
        <p className="mt-2 text-sm leading-6 text-muted">
          This page describes the behavior implemented in this build. It is not a claim of complete q coverage or of
          equivalence with kdb+.
        </p>
      </div>
      {sections.map((section) => (
        <section key={section.title}>
          <h2 className="text-lg font-medium">{section.title}</h2>
          <p className="mt-2 text-sm leading-6 text-muted">{section.body}</p>
        </section>
      ))}
    </div>
  );
}
