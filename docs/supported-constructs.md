# Supported constructs

A program is `supported` when every feature it uses is in `SUPPORTED_FEATURES` (`src/q2py/support.py`). It is `partial` when it uses a partial feature and nothing unsupported. Anything else the parser recognizes as out of scope, or fails to parse, is `unsupported` and produces no Python.

## Supported

- Literals: long, float, boolean, char, symbol, date, nulls (`0N`, `0n`, `0w`, `0W` where represented).
- Lists, strands, dictionaries, tables, and keyed tables built with `([] )` / `([ ] )` column syntax in the implemented form.
- Assignment, scripts, comments (`/` to end of line, and the block-comment form the lexer accepts).
- Lambdas with implicit `x`, `y`, `z`. Free names resolve to globals. Nested closures are not created.
- Projections, including holes.
- `$[cond;then;else]`.
- Infix arithmetic and comparison with right-to-left evaluation and no precedence. `%` is float division.
- `~` match, `^` fill, `,` join, `#` take, `_` drop, `?` find on lists, `in`.
- Prefix functions in the runtime: `til`, `count`, `sum`, `sums`, `avg`, `min`, `max`, `first`, `last`, `reverse`, `asc`, `desc`, `distinct`, `where`, `enlist`, `raze`, `abs`, `sqrt`, `type`, `string`, `flip`, `not`, `null`.
- Adverbs: each, each-left, each-right, each-prior, over, scan.
- `select`, `exec`, `update`, `delete` with `where` and simple `by` on the implemented table subset. `i` is the original row index.

## Partial

- Short, int, byte, real, month, and timestamp literals. The full q promotion and calendar arithmetic grids are not claimed.
- `div` and `mod`. Nonnegative cases are tested. Negatives raise a domain error at runtime.
- Converge: unary over without a do-count stops after 1000 iterations.

## Unsupported

- `|` and `&` as verbs, `.` amend/apply forms that are not indexing, and `$` cast.
- `peach`, `if`, `do`, `while`.
- Atom `?` (roll and deal), because it is non-deterministic.
- Any token the lexer does not recognize.

## Documented deviations

- `min` and `max` of an empty or all-null list raise domain. q returns negative or positive infinity.
- `avg` of a nested list is refused.
- Sum and sums treat flat numeric nulls as zero. `avg` ignores nulls. An empty or all-null average is a null float.
- `0N=0N` is false. `0N~0N` is true.
- Long arithmetic wraps in int64.
- Space is the null char.
