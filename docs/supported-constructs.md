# Supported constructs

A program is `supported` when every feature it uses is in `SUPPORTED_FEATURES` (`src/q2py/support.py`). It is `partial` when it uses a partial feature and nothing unsupported. Anything else the parser recognizes as out of scope, or fails to parse, is `unsupported` and produces no Python.

## Supported

- Literals: long, float, boolean (atoms and `01b` vectors), char, symbol, date, month (`2000.01m`), nulls (`0N`, `0Ni`, `0Nh`, `0n`), and infinities (`0w`, `-0w`, `0W`, `-0W`). A month plus or minus an integer shifts by that many months. Subtracting two months returns a long. A float offset is a type error.
- Lists, strands, dictionaries, tables, and keyed tables built with `([] )` / `([ ] )` column syntax in the implemented form.
- Assignment, scripts, comments (`/` to end of line, and the block-comment form the lexer accepts).
- Lambdas with implicit `x`, `y`, `z`. Free names resolve to globals. Nested closures are not created.
- Projections, including holes.
- `$[cond;then;else]`.
- Infix arithmetic and comparison with right-to-left evaluation and no precedence. `%` is float division.
- `~` match, `^` fill, `,` join, `#` take, `_` drop, `?` find on lists, `in`.
- Prefix functions in the runtime: `til`, `count`, `sum`, `sums`, `prd`, `prds`, `avg`, `med`, `var`, `dev`, `min`, `max`, `mins`, `maxs`, `all`, `any`, `first`, `last`, `reverse`, `asc`, `desc`, `iasc`, `idesc`, `distinct`, `where`, `enlist`, `raze`, `abs`, `sqrt`, `floor`, `ceiling`, `signum`, `prev`, `next`, `fills`, `differ`, `group`, `type`, `string`, `flip`, `not`, `null`, `cols`, `key`, `value` (dictionaries).
- Infix: `xbar`, `rotate`, `except`, `inter`, `union`, `div`, `mod`, greater `|`, and lesser `&`. `div` and `mod` are floor division: `x = (x div y) * y + (x mod y)`, and the remainder takes the sign of the divisor. Division by zero is a domain error. `|` returns the greater numeric value and `&` the lesser. Nulls sort below non-nulls. Two booleans stay boolean. A float or real widens the result to float. Symbols, chars, dates, months, and timestamps signal `type`.
- Adverbs: each, each-left, each-right, each-prior, over, scan. A parenthesized lambda may take a postfix adverb, as in `({x*y}/)`.
- `select`, `exec`, `update`, `delete` with `where` and simple `by` on the implemented table subset. `i` is the original row index.

## Partial

- Short, int, byte, real, and timestamp literals. `1h+2h` is short `3`. `32767h+1h` wraps to short `-32768`. `1h+1` is long `2`. A digit run ending in `i` is an int atom, the same suffix as `0Ni`. The bare name `i` is still the row index. The rest of the promotion grid, and timestamp arithmetic, are not claimed.
- Converge: unary over returns a fixed point reached within 1000 steps. If none is reached, it raises `limit` instead of looping.

## Unsupported

- `.` amend/apply forms that are not indexing, and `$` cast.
- `peach`, `if`, `do`, `while`.
- `system`, `read0`, `hopen`, `hclose`, `eval`, `load`, `save`, `reval`.
- Atom `?` (roll and deal), because it is non-deterministic.
- Function composition.
- Any token the lexer does not recognize.

## Documented deviations

- `min` and `max` of an empty or all-null list raise domain. q returns negative or positive infinity.
- `avg` of a nested list is refused.
- Sum and sums treat flat numeric nulls as zero. `avg` ignores nulls. An empty or all-null average is a null float.
- `0N=0N` is false. `0N~0N` is true.
- Long arithmetic wraps in int64.
- Space is the null char.
- `xbar` of a nonpositive size raises domain.
- `value` of anything other than a dictionary raises `unsupported` at runtime.
- `var` divides by n−1. `all` and `any` ignore nulls.
- Unary over on a lambda stops after 1000 iterations.

The rule statements are in `docs/q-semantics.md`.
