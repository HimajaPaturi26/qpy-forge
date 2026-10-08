# Q semantics in this subset

These are the rules the runtime implements. Expectations in the corpus were written from these rules, not by running the translator and copying its output.

## Evaluation

- There is no operator precedence. Expressions associate to the right.
- The left argument of an infix verb is the noun immediately on its left.
- A numeric vector binds before application.
- A slash after a blank or at the start of a line starts a comment. A line that is only `/` starts a block comment that ends at a line that is only `\`.
- A line that is only `\` ends the script.

## Atoms

- Longs wrap in int64. `0W` is 9223372036854775807. `-0W` is -9223372036854775808.
- `0w` and `-0w` are float infinities. `0n` is the null float. `0N`, `0Ni`, and `0Nh` are null long, int, and short.
- `%` is float division. `1%0` is positive infinity. `0%0` is a null float.
- A boolean vector literal is a run of `0` and `1` ending in `b`, such as `101b`. `0b` and `1b` stay atoms.
- `0N=0N` is false. `0N~0N` is true.
- Adding a long to a date moves that many days.

## Aggregates and running verbs

- `sum` and `sums` treat a flat numeric null as zero. An empty sum is 0.
- `prd` and `prds` treat a flat numeric null as one. An empty product is 1.
- `avg` ignores nulls. An empty or all-null average is a null float. Nested `avg` is refused.
- `min` and `max` ignore nulls. An empty or all-null list raises domain. q returns negative or positive infinity there.
- `mins` and `maxs` are the running minimum and maximum, ignoring nulls. A leading null stays null until a value appears.
- `all` is 1b when every non-null item is nonzero. Nulls are ignored. An empty list is 1b.
- `any` is 1b when any non-null item is nonzero. Nulls are ignored. An empty list is 0b.
- `med` ignores nulls and returns a float. An odd count uses the middle sorted value. An even count averages the two middle values. No values yields a null float.
- `var` is the sample variance (divide by n−1). `dev` is its square root. Fewer than two values yields a null float.

## Grades, shift, and sets

- `iasc` and `idesc` return indices. Ties keep the original order. Nulls sort first for `iasc` and last for `idesc`, matching `asc` and `desc`.
- `floor` and `ceiling` return longs. Float infinity floors and ceilings to `0W` or `-0W`.
- `signum` returns a long: −1, 0, or 1. A null input is a null long.
- `prev` shifts toward the tail and puts a null first. `next` shifts toward the head and puts a null last.
- `fills` copies the previous non-null forward. A leading null stays null.
- `differ` is 1b on the first item and 1b later when the item is not equal to the previous one. Nulls are not equal to each other under `=`.
- `x xbar y` is `x * floor(y % x)` for a positive bar size. A nonpositive size is a domain error.
- Positive `rotate` moves items left. Negative `rotate` moves them right.
- `except` drops left items that occur on the right. `inter` keeps left items that occur on the right, including duplicates. `union` keeps first-seen items from the left, then new items from the right.
- `group` maps each distinct item to the indices where it occurs, in first-seen order.

## Functions and iterators

- A lambda’s implicit arguments are `x`, or `x,y`, or `x,y,z`, from the highest of those names used.
- Nested lambdas do not close over locals. A free name is the global.
- A hole in a call builds a projection.
- `div` and `mod` are floor division. `x = (x div y)*y + (x mod y)` for `y` not zero. The remainder has the sign of `y`. `1 div 0` and `1 mod 0` are domain errors.
- `({x*y}/)` folds the list from the left. `({x*y}\)` keeps the scan. Unary over returns a fixed point reached within 1000 steps, such as `{x}/4` which is 4. If there is no fixed point, as with `{neg x}/1`, the result is the signal `limit`.
- each, each-left, each-right, and each-prior follow the same item-wise rules as the primitive adverbs.

## Tables

- `select`, `exec`, `update`, and `delete` see columns as vectors. `where` filters first. `i` is the original row index and is not renumbered.
- `by` groups in first-seen order. The result is a keyed table.
- `cols` is the symbol vector of column names. `key` of a dictionary is its keys. `key` of a keyed table is the key columns. `key` of an unkeyed table is an empty symbol vector.
- `value` is implemented for dictionaries. Other arguments raise `unsupported`.
- `flip` of a symbol-keyed column dictionary builds a table, one row per index.

## Refusals

`|`, `&`, `.` amend, `$` cast, `peach`, `if`, `do`, `while`, atom `?`, `system`, `read0`, `hopen`, `eval`, `load`, and `save` produce a diagnostic and no Python.
