# Limitations

- The in-scope language is a subset. Most of q, including the full qSQL dialect, interprocess communication, and the database, is unsupported.
- Semantic accuracy on the holdout corpus measures agreement with hand-authored JSON expectations. It does not prove equivalence to a kdb+ process.
- Expected values and the runtime were written from the same public description of q. Shared mistakes will not show up as failures.
- One each-right expectation follows the published each-left rule mirrored across the right argument. It was checked against that rule after an initial mismatch, and the case note records that. That case was not written blind to the translator.
- `flip`, keyed-table literals, and virtual `i` are implemented and covered by unit tests. They are not separate holdout cases, so a holdout-only construct table can omit them.
- `if`, `do`, `while`, and `peach` are refused before code generation. Atom `?` on two literals is refused the same way. A dynamic atom `?` whose arguments are not literals still compiles to `q_find`, which raises at runtime instead of returning a value.
- The in-process corpus executor does not apply the subprocess resource limits.
- Source maps record q line and column for generated statements. They do not map every Python expression back to a character range.
- Polars is used for table filter and projection. Nested table cells and many temporal types are outside that path.
- Finding a `q` binary does not enable oracle execution. This build never sends source to q.
- The sandbox is a local safety boundary for development. It is not a multi-tenant production isolator. See `docs/security.md`.
