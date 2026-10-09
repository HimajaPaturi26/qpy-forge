"""Support classification for the in-scope q subset.

Semantic accuracy is computed only on holdout cases whose declared support is
``supported``. Partial and unsupported cases are reported separately.
"""

from __future__ import annotations

TARGET = 0.90
CORPUS_VERSION = "1.7.0"

# Constructs the engine claims to translate with q-equivalent results.
SUPPORTED_FEATURES: frozenset[str] = frozenset(
    {
        "literal-long",
        "literal-float",
        "literal-bool",
        "literal-char",
        "literal-symbol",
        "literal-date",
        "literal-month",
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
        "neg",
        "not",
        "null",
        "sqrt",
        "type",
        "string",
        "flip",
        "prd",
        "prds",
        "all",
        "any",
        "mins",
        "maxs",
        "iasc",
        "idesc",
        "floor",
        "ceiling",
        "signum",
        "prev",
        "next",
        "fills",
        "med",
        "var",
        "dev",
        "differ",
        "group",
        "cols",
        "key",
        "value",
        "xbar",
        "rotate",
        "except",
        "inter",
        "union",
        "div-int",
        "mod",
        "or",
        "and",
        "cast",
        "cross",
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
        "literal-timestamp",
        "converge",
    }
)

# Names that parse as variables and are refused before code generation.
REFUSED_NAMES: frozenset[str] = frozenset(
    {
        "if",
        "do",
        "while",
        "peach",
        "system",
        "read0",
        "hopen",
        "hclose",
        "eval",
        "load",
        "save",
        "reval",
    }
)

# Constructs the engine refuses on purpose. This is a registry, not a score.
DOCUMENTED_UNSUPPORTED: tuple[tuple[str, str], ...] = (
    ("dot", "Amend and general dot-apply are refused."),
    ("peach", "Parallel each is refused."),
    ("if", "if is refused. $[...] is the supported conditional."),
    ("do", "do is refused."),
    ("while", "while is refused."),
    ("roll-deal", "Atom ? is non-deterministic and refused."),
    ("system", "system is refused."),
    ("read0", "read0 is refused."),
    ("hopen", "hopen and hclose are refused."),
    ("eval", "eval is refused."),
    ("load-save", "load and save are refused."),
    ("composition", "Function composition is not in this subset."),
)

PARTIAL_NOTES: dict[str, str] = {
    "literal-short": "Short literals wrap at 16 bits. Short plus long promotes to long. The rest of the promotion grid is not claimed.",
    "literal-int": "Int literals use the i suffix, including 0Ni. The full promotion grid is not claimed.",
    "literal-byte": "Byte literals are represented as unsigned 0–255 without the full promotion grid.",
    "literal-real": "Real literals are stored as float32 then widened; real arithmetic is not claimed.",
    "literal-timestamp": "Timestamp literals are represented. Timestamp arithmetic is not claimed.",
    "converge": "Unary over returns the fixed point when one is reached within 1000 steps. Otherwise it raises limit. q can loop forever.",
}
