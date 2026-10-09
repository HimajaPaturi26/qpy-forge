const sections = [
  {
    title: "What is translated",
    body: "Long and float arithmetic, greater (|) and lesser (&), numeric $ cast, cross, booleans including 01b vectors, chars, symbols, dates, nulls and infinities, lists, dictionaries, simple tables, assignment, lambdas without nested closures, projections, conditionals, the each family, over and scan (including a parenthesized lambda), reductions such as prd, med, and var, and a small select/exec/update/delete subset. The full list is in docs/supported-constructs.md.",
  },
  {
    title: "What is refused",
    body: "Dot amend, peach, if/do/while, system, read0, hopen, eval, load, save, atom roll and deal, and any syntax the parser does not recognize. A refusal leaves the Python field empty. $ cast of a symbol or of text parsed as a number signals type at runtime.",
  },
  {
    title: "Partial",
    body: "Short, int, byte, real, and timestamp literals are represented. The rest of the promotion grid, and timestamp arithmetic, are not claimed. Unary over returns a fixed point within 1000 steps or raises limit. Partial cases are excluded from headline accuracy.",
  },
  {
    title: "Expected values",
    body: "corpus/cases.json is hand-authored. The scoring code rejects a provenance that starts with generated-by-translator. Agreement with those values is not the same as a q process confirming them.",
  },
  {
    title: "Execution",
    body: "Studio runs use a Python subprocess with a stripped environment, CPU and address-space limits, and an AST allow-list. Generated code may only call q2py.runtime. Corpus scoring uses the same allow-list in-process so a full holdout measurement stays practical.",
  },
  {
    title: "Oracle",
    body: "If q is not on PATH and Q2PY_Q_BIN is unset, every status surface says Oracle: unavailable. Finding q does not turn on live oracle execution in this build.",
  },
];

export default function DocsPage() {
  return (
    <div className="max-w-3xl space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Documentation</h1>
        <p className="mt-1 text-sm text-muted">
          Repository documents cover architecture, validation methodology, the type mapping, security, and deployment.
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
