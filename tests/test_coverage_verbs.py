"""Expectations for the coverage-expansion verbs.

Each expected value is the published q rule written out below, not a dump of
the translator.
"""

import math

import pytest

from q2py.pipeline import translate, validate

LONG = lambda n: {"t": "long", "v": n}  # noqa: E731
FLOAT = lambda n: {"t": "float", "v": n}  # noqa: E731
BOOL = lambda n: {"t": "bool", "v": n}  # noqa: E731
NULL_LONG = {"t": "long", "null": True}
NULL_FLOAT = {"t": "float", "null": True}
SYM = lambda text: {"t": "symbol", "v": text}  # noqa: E731


def L(*nums: int) -> dict[str, object]:
    return {"t": "list", "etype": "long", "v": [LONG(n) for n in nums]}


def F(*nums: float) -> dict[str, object]:
    return {"t": "list", "etype": "float", "v": [FLOAT(n) for n in nums]}


def B(*flags: bool) -> dict[str, object]:
    return {"t": "list", "etype": "bool", "v": [BOOL(flag) for flag in flags]}


def assert_value(source: str, expected: object) -> None:
    result = validate(source, expected)
    assert result.matched, (source, result.display, result.canon, result.signal, result.translation.python)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("prd 2 3 4", LONG(24)),
        ("prd 2 0N 4", LONG(8)),
        ("prd 0#1 2", LONG(1)),
        ("prd 1.5 2 4", FLOAT(12.0)),
        ("prds 2 3 4", L(2, 6, 24)),
        ("prds 2 0N 4", L(2, 2, 8)),
        ("prds 0N 2 3", L(1, 2, 6)),
        ("all 1 1 0 1", BOOL(False)),
        ("all 1 2 3", BOOL(True)),
        ("all 1 0N 2", BOOL(True)),
        ("all 0#0", BOOL(True)),
        ("any 0 0 0", BOOL(False)),
        ("any 0 0N 4", BOOL(True)),
        ("any 0#0", BOOL(False)),
        # Running min ignores the null and keeps 3 across the later 4. 2 then replaces it.
        ("mins 5 3 0N 4 2", L(5, 3, 3, 3, 2)),
        ("maxs 5 3 0N 4 2", L(5, 5, 5, 5, 5)),
        ("mins 0N 3 1", {"t": "list", "etype": "long", "v": [NULL_LONG, LONG(3), LONG(1)]}),
        ("iasc 3 1 4 2", L(1, 3, 0, 2)),
        ("idesc 3 1 4 2", L(2, 0, 3, 1)),
        ("iasc 2 0N 1", L(1, 2, 0)),
        ("iasc 2 1 2", L(1, 0, 2)),
        ("floor 4.7", LONG(4)),
        ("floor -4.7", LONG(-5)),
        ("floor 2 3", L(2, 3)),
        ("ceiling 4.2", LONG(5)),
        ("ceiling -4.2", LONG(-4)),
        ("ceiling 2.0", LONG(2)),
        ("signum -4.2 0 3", L(-1, 0, 1)),
        ("signum 0n", NULL_LONG),
        ("signum 0w", LONG(1)),
        ("signum -0w", LONG(-1)),
        ("prev 10 20 30", {"t": "list", "etype": "long", "v": [NULL_LONG, LONG(10), LONG(20)]}),
        ("next 10 20 30", {"t": "list", "etype": "long", "v": [LONG(20), LONG(30), NULL_LONG]}),
        ("fills 1 0N 0N 4 0N", L(1, 1, 1, 4, 4)),
        ("fills 0N 1 0N", {"t": "list", "etype": "long", "v": [NULL_LONG, LONG(1), LONG(1)]}),
        ("differ 1 2 2 3", B(True, True, False, True)),
        ("5 xbar 1 3 8 10", L(0, 0, 5, 10)),
        ("5 xbar 12", LONG(10)),
        ("2 rotate 1 2 3 4 5", L(3, 4, 5, 1, 2)),
        ("-2 rotate 1 2 3 4 5", L(4, 5, 1, 2, 3)),
        ("1 2 2 3 except 2 9", L(1, 3)),
        ("1 2 2 3 inter 2 4", L(2, 2)),
        ("1 1 2 union 2 3 3", L(1, 2, 3)),
        ("med 1 2 100", FLOAT(2.0)),
        ("med 1 2 3 4", FLOAT(2.5)),
        ("med 0N", NULL_FLOAT),
        ("var 2 3 4 5", FLOAT(5.0 / 3.0)),
        ("dev 2 3 4 5", FLOAT(math.sqrt(5.0 / 3.0))),
        ("var 2", NULL_FLOAT),
        ("0W", LONG(9223372036854775807)),
        ("-0W", LONG(-9223372036854775808)),
        ("1+0w", {"t": "float", "v": "inf"}),
        ("0n+1", NULL_FLOAT),
        ("null 0Ni", BOOL(True)),
        ("type 0Ni", {"t": "short", "v": -6}),
        ("type 0Nh", {"t": "short", "v": -5}),
    ],
)
def test_new_verbs(source: str, expected: object) -> None:
    assert_value(source, expected)


def test_group_preserves_first_seen_keys() -> None:
    result = validate("group 1 2 1 3")
    assert result.canon == {
        "t": "dict",
        "keys": [LONG(1), LONG(2), LONG(3)],
        "vals": [L(0, 2), L(1), L(3)],
    }, result.canon


def test_cols_and_key_value() -> None:
    cols = validate("t:([] a:1 2; b:3 4)\ncols t")
    assert cols.canon == {
        "t": "list",
        "etype": "symbol",
        "v": [SYM("a"), SYM("b")],
    }, cols.canon
    keys = validate("key `a`b!1 2")
    assert keys.canon == {"t": "list", "etype": "symbol", "v": [SYM("a"), SYM("b")]}, keys.canon
    vals = validate("value `a`b!10 20")
    assert vals.canon == L(10, 20), vals.canon
    key_table = validate("key ([k:1 2] v:10 20)")
    assert key_table.canon is not None
    assert key_table.canon["cols"] == ["k"]
    assert [row["k"]["v"] for row in key_table.canon["rows"]] == [1, 2]


def test_flip_keyed_and_virtual_i_stay_available() -> None:
    flipped = validate("flip `a`b!(1 2;3 4)")
    assert flipped.canon is not None
    assert flipped.canon["rows"] == [{"a": LONG(1), "b": LONG(3)}, {"a": LONG(2), "b": LONG(4)}]
    keyed = validate("([k:1 2] v:10 20)")
    assert keyed.canon is not None
    assert keyed.canon["keys"] == ["k"]
    virtual = validate("t:([] a:10 20)\nselect i from t where i=1")
    assert virtual.canon is not None
    assert virtual.canon["rows"] == [{"i": LONG(1)}]


def test_select_avg_and_count_by() -> None:
    averaged = validate("t:([] a:1 2 3)\nselect avg a from t")
    assert averaged.canon is not None
    assert averaged.canon["rows"] == [{"a": FLOAT(2.0)}], averaged.canon
    counted = validate("t:([] b:`x`y`x; a:1 2 3)\nselect count a by b from t")
    assert counted.canon is not None
    assert counted.canon["rows"] == [
        {"b": SYM("x"), "a": LONG(2)},
        {"b": SYM("y"), "a": LONG(1)},
    ], counted.canon


@pytest.mark.parametrize(
    "source",
    ["system \"ls\"", "read0 `:data", "hopen `:host:1", "eval 1", "peach 1", "if 1", "do 1", "while 1", "1?2"],
)
def test_refusals_emit_no_python(source: str) -> None:
    result = translate(source)
    assert result.support == "unsupported", (source, result.support, result.python)
    assert result.python == ""


def test_boolean_vector_literal_and_lambda_fold() -> None:
    assert_value("all 101b", BOOL(False))
    assert_value("any 010b", BOOL(True))
    assert_value("where 000b", {"t": "list", "etype": "general", "v": []})
    assert_value("({x*y}/)1 2 3 4", LONG(24))
    assert_value("({x*y}\\)1 2 3 4", L(1, 2, 6, 24))
    converged = translate("{x}/1")
    assert converged.support == "partial"
    assert validate("{x}/1", LONG(1)).matched


def test_infinity_literal_is_a_float_constant() -> None:
    translated = translate("signum 0w")
    assert "inf)" not in translated.python
    assert "1e309" in translated.python
    assert_value("signum 0w", LONG(1))
    assert_value("floor 0w", LONG(9223372036854775807))
    assert_value("floor -0w", LONG(-9223372036854775808))


def test_negative_xbar_is_domain() -> None:
    result = validate("-5 xbar 10", expected_signal="domain")
    assert result.matched is True
    assert result.signal == "domain"


def test_expansion_keeps_the_protected_holdout() -> None:
    from q2py.metrics import measure

    holdout = measure("holdout")
    dev = measure("dev")
    coverage = measure("coverage")
    assert holdout["corpus_version"] == "1.6.0"
    assert holdout["corpus_counts"]["all"] >= 200
    assert holdout["corpus_counts"]["holdout"] == 95
    assert holdout["sample_size"] == 95
    assert holdout["successes"] == 95
    assert holdout["semantic_accuracy"] == 1.0
    assert holdout["oracle_match_rate"] is None
    assert dev["sample_size"] == dev["successes"]
    assert dev["sample_size"] == 145
    assert coverage["rows"]
    assert all(row["matched"] for row in coverage["rows"])


def test_value_of_a_non_dict_is_refused_at_runtime() -> None:
    result = validate('value "1+1"', expected_signal="unsupported")
    assert result.matched is True
    assert result.translation.python != ""
