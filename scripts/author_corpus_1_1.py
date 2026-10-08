"""Append the 1.1.0 corpus cases.

Expected values are written from published q rules. This script does not call
the translator.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "corpus" / "cases.json"
PROV = "hand-authored from published q evaluation rules; not produced by the translator"


def long(n: int) -> dict[str, object]:
    return {"t": "long", "v": n}


def fl(n: float | str) -> dict[str, object]:
    return {"t": "float", "v": n}


def bo(flag: bool) -> dict[str, object]:
    return {"t": "bool", "v": flag}


def short(n: int) -> dict[str, object]:
    return {"t": "short", "v": n}


def integer(n: int) -> dict[str, object]:
    return {"t": "int", "v": n}


def sym(text: str) -> dict[str, object]:
    return {"t": "symbol", "v": text}


def nlong() -> dict[str, object]:
    return {"t": "long", "null": True}


def nfloat() -> dict[str, object]:
    return {"t": "float", "null": True}


def nsym() -> dict[str, object]:
    return {"t": "symbol", "null": True}


def chars(text: str) -> dict[str, object]:
    return {"t": "list", "etype": "char", "v": [{"t": "char", "v": ch} for ch in text]}


def longs(*nums: int) -> dict[str, object]:
    return {"t": "list", "etype": "long", "v": [long(n) for n in nums]}


def floats(*nums: float) -> dict[str, object]:
    return {"t": "list", "etype": "float", "v": [fl(n) for n in nums]}


def bools(*flags: bool) -> dict[str, object]:
    return {"t": "list", "etype": "bool", "v": [bo(flag) for flag in flags]}


def symbols(*names: str) -> dict[str, object]:
    return {"t": "list", "etype": "symbol", "v": [sym(name) for name in names]}


def general(*items: dict[str, object]) -> dict[str, object]:
    return {"t": "list", "etype": "general", "v": list(items)}


def table(cols: list[str], types: dict[str, str], rows: list[dict[str, object]], keys: list[str] | None = None) -> dict[str, object]:
    return {
        "t": "keyed" if keys else "table",
        "keys": keys or [],
        "cols": cols,
        "types": types,
        "rows": rows,
    }


def case(
    case_id: str,
    source: str,
    features: list[str],
    *,
    split: str = "dev",
    support: str = "supported",
    expected: object | None = None,
    expected_signal: str | None = None,
    expect_support: str | None = None,
    note: str = "",
) -> dict[str, object]:
    item: dict[str, object] = {
        "id": case_id,
        "split": split,
        "support": support,
        "features": features,
        "source": source,
        "provenance": PROV,
        "note": note,
    }
    if expected is not None:
        item["expected"] = expected
    if expected_signal is not None:
        item["expected_signal"] = expected_signal
    if expect_support is not None:
        item["expect_support"] = expect_support
    return item


def dev(case_id: str, source: str, features: list[str], expected: object, note: str = "") -> dict[str, object]:
    return case(case_id, source, features, expected=expected, note=note)


def refusal(case_id: str, source: str, features: list[str], note: str) -> dict[str, object]:
    return case(
        case_id,
        source,
        features,
        split="coverage",
        support="unsupported",
        expect_support="unsupported",
        note=note,
    )


VAR = 5.0 / 3.0
DEV = math.sqrt(VAR)

NEW: list[dict[str, object]] = [
    dev("dev-prd", "prd 2 3 4", ["prd"], long(24), "Product 2*3*4 is 24."),
    dev("dev-prd-null", "prd 2 0N 4", ["prd", "literal-null"], long(8), "prd treats a flat null as the identity 1."),
    dev("dev-prd-empty", "prd 0#8 9", ["prd", "take"], long(1), "The empty product is 1."),
    dev("dev-prd-float", "prd 1.5 2 4.0", ["prd", "literal-float"], fl(12.0), "1.5*2*4 is 12."),
    dev("dev-prds", "prds 2 3 4", ["prds"], longs(2, 6, 24), "Running product."),
    dev("dev-prds-null", "prds 2 0N 4", ["prds"], longs(2, 2, 8), "A null is the identity, so the running product stays 2 then becomes 8."),
    dev("dev-prds-lead-null", "prds 0N 2 3", ["prds"], longs(1, 2, 6), "A leading null starts the running product at 1."),
    dev("dev-all-zero", "all 1 1 0 1", ["all"], bo(False), "all is 0b when any item is zero."),
    dev("dev-all-nonzero", "all 1 2 3", ["all"], bo(True), "all is 1b when every item is nonzero."),
    dev("dev-all-null", "all 1 0N 2", ["all"], bo(True), "all ignores nulls. No zero remains."),
    dev("dev-all-empty", "all 0#9", ["all"], bo(True), "all of an empty list is 1b."),
    dev("dev-all-bool", "all 101b", ["all", "literal-bool"], bo(False), "A false boolean makes all false."),
    dev("dev-any-zero", "any 0 0 0", ["any"], bo(False), "any is 0b when every item is zero."),
    dev("dev-any-null", "any 0 0N 4", ["any"], bo(True), "any ignores nulls and sees the 4."),
    dev("dev-any-empty", "any 0#9", ["any"], bo(False), "any of an empty list is 0b."),
    dev("dev-any-bool", "any 010b", ["any"], bo(True), "One true boolean makes any true."),
    dev(
        "dev-mins",
        "mins 5 3 0N 4 2",
        ["mins"],
        longs(5, 3, 3, 3, 2),
        "Running min ignores the null. 4 does not replace 3. 2 does.",
    ),
    dev("dev-maxs", "maxs 5 3 0N 4 2", ["maxs"], longs(5, 5, 5, 5, 5), "Running max ignores the null and stays 5."),
    dev(
        "dev-mins-lead-null",
        "mins 0N 3 1",
        ["mins"],
        {"t": "list", "etype": "long", "v": [nlong(), long(3), long(1)]},
        "A leading null stays null until a value arrives.",
    ),
    dev("dev-iasc", "iasc 3 1 4 2", ["iasc"], longs(1, 3, 0, 2), "Indices that sort 3 1 4 2 ascending."),
    dev("dev-idesc", "idesc 3 1 4 2", ["idesc"], longs(2, 0, 3, 1), "Indices that sort 3 1 4 2 descending."),
    dev("dev-iasc-null", "iasc 2 0N 1", ["iasc"], longs(1, 2, 0), "Nulls sort first, matching asc."),
    dev("dev-iasc-stable", "iasc 2 1 2", ["iasc"], longs(1, 0, 2), "Equal items keep their original order."),
    dev("dev-iasc-sym", "iasc `c`a`b", ["iasc", "literal-symbol"], longs(1, 2, 0), "Symbol grade follows alphabetical order."),
    dev("dev-floor", "floor 4.7", ["floor"], long(4), "floor rounds toward negative infinity."),
    dev("dev-floor-neg", "floor -4.7", ["floor"], long(-5), "floor of -4.7 is -5."),
    dev("dev-floor-int", "floor 2 3", ["floor"], longs(2, 3), "floor of an integer vector is that vector as longs."),
    dev("dev-floor-inf", "floor 0w", ["floor"], long(9223372036854775807), "floor of positive float infinity is 0W."),
    dev("dev-floor-ninf", "floor -0w", ["floor"], long(-9223372036854775808), "floor of negative float infinity is -0W."),
    dev("dev-ceiling", "ceiling 4.2", ["ceiling"], long(5), "ceiling rounds toward positive infinity."),
    dev("dev-ceiling-neg", "ceiling -4.2", ["ceiling"], long(-4), "ceiling of -4.2 is -4."),
    dev("dev-ceiling-whole", "ceiling 2.0", ["ceiling"], long(2), "A whole float ceilings to itself."),
    dev("dev-signum", "signum -4.2 0 3", ["signum"], longs(-1, 0, 1), "signum returns -1, 0, or 1 as longs."),
    dev("dev-signum-null", "signum 0n", ["signum"], nlong(), "signum of a null float is a null long."),
    dev("dev-signum-inf", "signum 0w", ["signum"], long(1), "Positive infinity has sign 1."),
    dev("dev-signum-ninf", "signum -0w", ["signum"], long(-1), "Negative infinity has sign -1."),
    dev(
        "dev-prev",
        "prev 10 20 30",
        ["prev"],
        {"t": "list", "etype": "long", "v": [nlong(), long(10), long(20)]},
        "prev shifts right and fills the first item with null.",
    ),
    dev(
        "dev-next",
        "next 10 20 30",
        ["next"],
        {"t": "list", "etype": "long", "v": [long(20), long(30), nlong()]},
        "next shifts left and fills the last item with null.",
    ),
    dev("dev-fills", "fills 1 0N 0N 4 0N", ["fills"], longs(1, 1, 1, 4, 4), "fills carries the last non-null forward."),
    dev(
        "dev-fills-lead",
        "fills 0N 1 0N",
        ["fills"],
        {"t": "list", "etype": "long", "v": [nlong(), long(1), long(1)]},
        "A leading null has nothing to copy.",
    ),
    dev("dev-fills-float", "fills 1.5 0n 2.5", ["fills"], floats(1.5, 1.5, 2.5), "Forward fill on floats."),
    dev("dev-differ", "differ 1 2 2 3", ["differ"], bools(True, True, False, True), "First item differs. Later items differ when they are not equal to the previous."),
    dev("dev-differ-sym", "differ `a`a`b", ["differ"], bools(True, False, True), "`a equals the previous `a, so that item is 0b."),
    dev("dev-xbar", "5 xbar 1 3 8 10", ["xbar"], longs(0, 0, 5, 10), "Round each item down to a multiple of 5."),
    dev("dev-xbar-atom", "5 xbar 12", ["xbar"], long(10), "12 rounded down to a multiple of 5 is 10."),
    dev("dev-xbar-float", "2.5 xbar 0 2.5 5 6", ["xbar"], floats(0.0, 2.5, 5.0, 5.0), "6/2.5 is 2.4, which floors to 2, times 2.5 is 5."),
    dev("dev-rotate", "2 rotate 1 2 3 4 5", ["rotate"], longs(3, 4, 5, 1, 2), "Positive rotate moves items left."),
    dev("dev-rotate-neg", "-2 rotate 1 2 3 4 5", ["rotate"], longs(4, 5, 1, 2, 3), "Negative rotate moves items right."),
    dev("dev-rotate-zero", "0 rotate 8 9 10", ["rotate"], longs(8, 9, 10), "A zero rotate is the identity."),
    dev("dev-except", "1 2 2 3 except 2 9", ["except"], longs(1, 3), "Drop every item of the left that occurs on the right."),
    dev("dev-inter", "1 2 2 3 inter 2 4", ["inter"], longs(2, 2), "Keep left items that occur on the right, including duplicates."),
    dev("dev-union", "1 1 2 union 2 3 3", ["union"], longs(1, 2, 3), "Distinct left items, then new right items."),
    dev("dev-union-sym", "`a`b union `b`c", ["union"], symbols("a", "b", "c"), "Symbol union keeps first-seen order."),
    dev("dev-med-odd", "med 1 2 100", ["med"], fl(2.0), "Median of an odd count is the middle value as a float."),
    dev("dev-med-even", "med 1 2 3 4", ["med"], fl(2.5), "Median of an even count is the mean of the two middle values."),
    dev("dev-med-null", "med 0N", ["med"], nfloat(), "A null has no median."),
    dev("dev-var", "var 2 3 4 5", ["var"], fl(VAR), "Sample variance: sum of squared deviations from 3.5, divided by 3."),
    dev("dev-dev", "dev 2 3 4 5", ["dev"], fl(DEV), "dev is the square root of the sample variance."),
    dev("dev-var-short", "var 2", ["var"], nfloat(), "Sample variance needs at least two numbers."),
    dev("dev-0w", "0W", ["literal-long"], long(9223372036854775807), "0W is the maximum signed long."),
    dev("dev-neg-0w", "-0W", ["literal-long"], long(-9223372036854775808), "-0W is the minimum signed long."),
    dev("dev-add-inf", "3+0w", ["infix-arith", "literal-float"], fl("inf"), "A long plus positive float infinity is positive infinity."),
    dev("dev-add-null-float", "0n+4", ["infix-arith", "literal-null"], nfloat(), "A null float absorbs addition."),
    dev("dev-null-int", "null 0Ni", ["null", "literal-null"], bo(True), "0Ni is the null int."),
    dev("dev-type-int-null", "type 0Ni", ["type"], short(-6), "An int atom has type -6h."),
    dev("dev-type-short-null", "type 0Nh", ["type"], short(-5), "A short atom has type -5h."),
    dev("dev-type-float", "type 1.5", ["type"], short(-9), "A float atom has type -9h."),
    dev(
        "dev-group",
        "group 1 2 1 3",
        ["group"],
        {"t": "dict", "keys": [long(1), long(2), long(3)], "vals": [longs(0, 2), longs(1), longs(3)]},
        "group maps each distinct item to the indices where it occurs, in first-seen order.",
    ),
    dev(
        "dev-group-sym",
        "group `a`b`a",
        ["group"],
        {"t": "dict", "keys": [sym("a"), sym("b")], "vals": [longs(0, 2), longs(1)]},
        "Symbol group keeps first-seen keys.",
    ),
    dev(
        "dev-cols",
        "t:([] a:1 2; b:3 4)\ncols t",
        ["cols", "table"],
        symbols("a", "b"),
        "cols returns the column names as symbols.",
    ),
    dev("dev-key-dict", "key `a`b!1 2", ["key", "dict"], symbols("a", "b"), "key of a dictionary is its key list."),
    dev("dev-value-dict", "value `c`d!10 20", ["value", "dict"], longs(10, 20), "value of a dictionary is its value list."),
    dev(
        "dev-key-keyed",
        "key ([k:1 2] v:10 20)",
        ["key", "keyed-table"],
        table(["k"], {"k": "long"}, [{"k": long(1)}, {"k": long(2)}]),
        "key of a keyed table is the table of key columns.",
    ),
    dev(
        "dev-key-unkeyed",
        "key ([] a:7 8)",
        ["key", "table"],
        {"t": "list", "etype": "symbol", "v": []},
        "An unkeyed table has an empty symbol vector of keys.",
    ),
    dev(
        "dev-flip",
        "flip `a`b!(1 2;3 4)",
        ["flip", "dict"],
        table(["a", "b"], {"a": "long", "b": "long"}, [{"a": long(1), "b": long(3)}, {"a": long(2), "b": long(4)}]),
        "flip of a column dictionary builds one row per index.",
    ),
    dev(
        "dev-keyed",
        "([k:1 2] v:10 20)",
        ["keyed-table"],
        table(["k", "v"], {"k": "long", "v": "long"}, [{"k": long(1), "v": long(10)}, {"k": long(2), "v": long(20)}], ["k"]),
        "A keyed table literal keeps the names inside the brackets as keys.",
    ),
    dev(
        "dev-virtual-i",
        "t:([] a:10 20)\nselect i from t where i=1",
        ["virtual-i", "select"],
        table(["i"], {"i": "long"}, [{"i": long(1)}]),
        "where does not renumber i. The surviving row keeps index 1.",
    ),
    dev(
        "dev-select-avg",
        "t:([] a:1 2 3)\nselect avg a from t",
        ["select", "avg"],
        table(["a"], {"a": "float"}, [{"a": fl(2.0)}]),
        "avg of 1 2 3 is 2.",
    ),
    dev(
        "dev-select-min",
        "t:([] a:2 4 6)\nselect min a from t",
        ["select", "min"],
        table(["a"], {"a": "long"}, [{"a": long(2)}]),
        "min of 2 4 6 is 2.",
    ),
    dev(
        "dev-select-max",
        "t:([] a:2 4 6)\nselect max a from t",
        ["select", "max"],
        table(["a"], {"a": "long"}, [{"a": long(6)}]),
        "max of 2 4 6 is 6.",
    ),
    dev(
        "dev-select-prd",
        "t:([] a:2 4 6)\nselect prd a from t",
        ["select", "prd"],
        table(["a"], {"a": "long"}, [{"a": long(48)}]),
        "prd of 2 4 6 is 48.",
    ),
    dev(
        "dev-select-count-by",
        "t:([] b:`x`y`x; a:1 2 3)\nselect count a by b from t",
        ["select", "by", "count"],
        table(
            ["b", "a"],
            {"b": "symbol", "a": "long"},
            [{"b": sym("x"), "a": long(2)}, {"b": sym("y"), "a": long(1)}],
            ["b"],
        ),
        "count by preserves first-seen group order. x occurs twice.",
    ),
    dev(
        "dev-select-floor",
        "t:([] a:1.2 2.8)\nselect floor a from t",
        ["select", "floor"],
        table(["a"], {"a": "long"}, [{"a": long(1)}, {"a": long(2)}]),
        "floor is applied to the column vector.",
    ),
    dev(
        "dev-delete-col",
        "t:([] a:1 2; b:3 4)\ndelete b from t",
        ["delete"],
        table(["a"], {"a": "long"}, [{"a": long(1)}, {"a": long(2)}]),
        "delete of a column name drops that column.",
    ),
    dev(
        "dev-update-where",
        "t:([] a:1 2 3)\nupdate a:a*10 from t where a>1",
        ["update"],
        table(["a"], {"a": "long"}, [{"a": long(1)}, {"a": long(20)}, {"a": long(30)}]),
        "update where changes only the rows that pass the filter.",
    ),
    dev(
        "dev-exec-one",
        "t:([] a:4 5)\nexec a from t",
        ["exec"],
        longs(4, 5),
        "exec of one column returns that vector.",
    ),
    dev("dev-each-floor", "floor each 1.2 3.8", ["each", "floor"], longs(1, 3), "each applies floor to every item."),
    dev("dev-over-mul", "({x*y}/)1 2 3 4", ["over", "lambda"], long(24), "Over multiplies 1*2*3*4."),
    dev("dev-lambda-prd", "f:{prd x}\nf 2 5", ["lambda", "prd"], long(10), "A named function can call prd."),
    dev("dev-proj-hole", "{x+y}[;10] 3", ["projection", "lambda"], long(13), "The elided first argument is filled by the later call."),
    dev("dev-bool-add", "1b+1b", ["infix-arith", "literal-bool"], integer(2), "Boolean addition promotes to int."),
    dev("dev-float-lt", "1.5<2.5", ["infix-compare"], bo(True), "Float less-than."),
    dev("dev-date-roll", "2020.12.31+1", ["infix-arith", "literal-date"], {"t": "date", "v": "2021-01-01"}, "Adding 1 to a date moves one day."),
    dev("dev-sym-in", "`b in `a`b`c", ["in", "literal-symbol"], bo(True), "A symbol is in a symbol vector when one item matches."),
    dev("dev-count-dict", "count `a`b!1 2", ["count", "dict"], long(2), "A dictionary's count is its number of entries."),
    dev("dev-reverse-sym", "reverse `a`b`c", ["reverse"], symbols("c", "b", "a"), "reverse keeps the symbol type."),
    dev("dev-string-long", "string 42", ["string"], chars("42"), "string of a long is its decimal digits."),
    dev("dev-sqrt-zero", "sqrt 0", ["sqrt"], fl(0.0), "sqrt of zero is zero."),
    dev("dev-abs-float", "abs -1.5", ["abs"], fl(1.5), "abs of a negative float is the positive float."),
    dev(
        "dev-mixed-list",
        "(1;2.0;`a)",
        ["list"],
        general(long(1), fl(2.0), sym("a")),
        "A semicolon list keeps mixed types.",
    ),
    dev("dev-nested-count", "count (1 2;3 4)", ["count", "list"], long(2), "count of a nested list is the number of items, not the flattened length."),
    dev("dev-index-nested", "(1 2;3 4)[1]", ["list", "apply"], longs(3, 4), "Indexing a nested list returns that item."),
    dev(
        "dev-prev-sym",
        "prev `a`b",
        ["prev"],
        {"t": "list", "etype": "symbol", "v": [nsym(), sym("a")]},
        "prev of symbols uses the null symbol.",
    ),
    dev("dev-comment-block", "/\n1+1\n\\\n2+2", ["comment", "infix-arith"], long(4), "A block comment from a lone slash to a lone backslash is skipped."),
    dev("dev-script-assign", "a:10\nb:a+5\nb*2", ["script", "assign"], long(30), "Later statements see earlier assignments. 15*2 is 30."),
    dev("dev-not-zero", "not 0 5", ["not"], bools(True, False), "not is 1b only for zero."),
    dev("dev-null-vector", "null 1 0N 2", ["null"], bools(False, True, False), "null is item-wise."),
    dev("dev-where-empty", "where 000b", ["where"], {"t": "list", "etype": "general", "v": []}, "where of no true items is an empty index list."),
    dev("dev-take-neg-atom", "-1#10 20 30", ["take"], longs(30), "Negative take keeps the tail."),
    dev("dev-drop-tail", "-1_10 20 30", ["drop"], longs(10, 20), "Negative drop removes the tail."),
    dev("dev-join-atom", "1,2 3", ["join"], longs(1, 2, 3), "Join enlists an atom on the left."),
    dev("dev-find-first", "1 2 2 3?2", ["find"], long(1), "find returns the first index."),
    dev("dev-match-list-no", "1 2~1 3", ["match"], bo(False), "Lists match only when every item matches."),
    dev("dev-fill-atom", "7^0N", ["fill"], long(7), "Fill replaces a null atom."),
    dev("dev-cond-mid", "$[0b;1;1b;2;3]", ["cond"], long(2), "The first true test selects its branch."),
    dev("dev-lambda-xyz", "{x+y+z}[1;2;3]", ["lambda"], long(6), "An implicit three-argument lambda uses x, y, and z."),
    dev("dev-each-left-sub", "10 20-\\:1 2", ["each-left"], general(longs(9, 8), longs(19, 18)), "Each left item is subtracted by the whole right list."),
    dev("dev-scan-mul", "({x*y}\\)1 2 3 4", ["scan", "lambda"], longs(1, 2, 6, 24), "Scan keeps each running product."),
    dev("dev-enlist-sym", "enlist `a", ["enlist"], symbols("a"), "enlist of a symbol is a one-item symbol vector."),
    dev("dev-distinct-sym", "distinct `a`b`a", ["distinct"], symbols("a", "b"), "distinct keeps the first of each symbol."),
    dev("dev-desc-sym", "desc `a`c`b", ["desc"], symbols("c", "b", "a"), "desc sorts symbols reverse alphabetically."),
    refusal("cov-and", "2&3", ["and"], "The & verb is refused."),
    refusal("cov-cast", '"i"$10', ["cast"], "Cast with $ is refused."),
    refusal("cov-dot", "1 2 3 . 0", ["dot"], "Dot apply is refused."),
    refusal("cov-peach", "peach 1", ["peach"], "peach is refused."),
    refusal("cov-if", "if 1", ["if"], "if is refused."),
    refusal("cov-do", "do 1", ["do"], "do is refused."),
    refusal("cov-while", "while 1", ["while"], "while is refused."),
    refusal("cov-roll", "1?2", ["find"], "Atom roll is refused."),
    refusal("cov-system", 'system "ls"', ["system"], "system is refused."),
    refusal("cov-read0", "read0 `data", ["read0"], "read0 is refused."),
    refusal("cov-hopen", "hopen `host", ["hopen"], "hopen is refused."),
    refusal("cov-eval", "eval 1", ["eval"], "eval is refused."),
    refusal("cov-load", "load `data", ["load"], "load is refused."),
    refusal("cov-save", "save `data", ["save"], "save is refused."),
    refusal("cov-reval", "reval 1", ["reval"], "reval is refused."),
    case(
        "cov-mod",
        "7 mod 3",
        ["mod"],
        split="coverage",
        support="partial",
        expected=long(1),
        note="7 divided by 3 leaves remainder 1. mod stays partial because negatives are domain errors.",
    ),
    case(
        "cov-div-seven",
        "7 div 3",
        ["div-int"],
        split="coverage",
        support="partial",
        expected=long(2),
        note="Integer division of 7 by 3 is 2.",
    ),
    case(
        "cov-div-neg",
        "-5 div 2",
        ["div-int"],
        split="coverage",
        support="partial",
        expected_signal="domain",
        note="Negative div is a domain error in this subset.",
    ),
    case(
        "cov-xbar-neg",
        "-5 xbar 10",
        ["xbar"],
        split="coverage",
        support="supported",
        expected_signal="domain",
        note="A nonpositive xbar size is a domain error.",
    ),
    case(
        "cov-value-string",
        'value "1+1"',
        ["value"],
        split="coverage",
        support="supported",
        expected_signal="unsupported",
        note="value is implemented for dictionaries. A character vector is refused at runtime.",
    ),
    case(
        "cov-sqrt-neg",
        "sqrt -1",
        ["sqrt"],
        split="coverage",
        support="supported",
        expected_signal="domain",
        note="sqrt of a negative number is a domain error.",
    ),
]


def main() -> None:
    payload = json.loads(PATH.read_text(encoding="utf-8"))
    existing = payload["cases"]
    ids = {item["id"] for item in existing}
    sources = {item["source"] for item in existing}
    for item in NEW:
        if item["id"] in ids:
            raise SystemExit(f"duplicate id {item['id']}")
        if item["source"] in sources:
            raise SystemExit(f"duplicate source for {item['id']}: {item['source']}")
        ids.add(str(item["id"]))
        sources.add(str(item["source"]))
    payload["version"] = "1.1.0"
    payload["cases"] = existing + NEW
    PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"cases {len(existing)} -> {len(payload['cases'])}")


if __name__ == "__main__":
    main()
