"""Support classification for the in-scope q subset.

Semantic accuracy is computed only on holdout cases whose declared support is
``supported``. Partial and unsupported cases are reported separately.
"""

from __future__ import annotations

TARGET = 0.90
CORPUS_VERSION = "1.0.0"

# Constructs the engine claims to translate with q-equivalent results.
SUPPORTED_FEATURES: frozenset[str] = frozenset(
    {
        "literal-long",
        "literal-float",
        "literal-bool",
        "literal-char",
        "literal-symbol",
        "literal-date",
        "literal-null",
        "strand",
        "list",
        "dict",
        "table",
        "keyed-table",
        "assign",
        "script",
        "lambda",
        "projection",
        "cond",
        "comment",
        "infix-arith",
        "infix-compare",
        "match",
        "fill",
        "join",
        "take",
        "drop",
        "find",
        "in",
        "apply",
        "prefix",
        "til",
        "count",
        "sum",
        "sums",
        "avg",
        "min",
        "max",
        "first",
        "last",
        "reverse",
        "asc",
        "desc",
        "distinct",
        "where",
        "enlist",
        "raze",
        "abs",
        "sqrt",
        "type",
        "string",
        "flip",
        "each",
        "each-left",
        "each-right",
        "each-prior",
        "over",
        "scan",
        "select",
        "exec",
        "update",
        "delete",
        "by",
        "virtual-i",
    }
)

# Translated, but with a documented semantic gap. Excluded from the accuracy denominator
# when a case is tagged partial. Using one of these features marks a program partial.
PARTIAL_FEATURES: frozenset[str] = frozenset(
    {
        "literal-short",
        "literal-int",
        "literal-byte",
        "literal-real",
        "literal-month",
        "literal-timestamp",
        "div-int",
        "mod",
        "converge",
    }
)

PARTIAL_NOTES: dict[str, str] = {
    "literal-short": "Short literals are represented, but the full q promotion grid is not claimed.",
    "literal-int": "Int literals are represented, but the full q promotion grid is not claimed.",
    "literal-byte": "Byte literals are represented as unsigned 0–255 without the full promotion grid.",
    "literal-real": "Real literals are stored as float32 then widened; real arithmetic is not claimed.",
    "literal-month": "Month literals are represented. Month arithmetic is not claimed.",
    "literal-timestamp": "Timestamp literals are represented. Timestamp arithmetic is not claimed.",
    "div-int": "div/mod on negative integers are refused at runtime (domain). Only nonnegative behavior is tested.",
    "mod": "div/mod on negative integers are refused at runtime (domain). Only nonnegative behavior is tested.",
    "converge": "Unary over without an explicit do-count stops at 1000 iterations instead of looping forever.",
}
