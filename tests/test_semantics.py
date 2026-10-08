import datetime as dt

import pytest

from q2py.pipeline import validate

LONG = lambda n: {"t": "long", "v": n}  # noqa: E731
FLOAT = lambda n: {"t": "float", "v": n}  # noqa: E731
BOOL = lambda n: {"t": "bool", "v": n}  # noqa: E731
NULL_LONG = {"t": "long", "null": True}
NULL_FLOAT = {"t": "float", "null": True}


def L(*nums: int) -> dict[str, object]:
    return {"t": "list", "etype": "long", "v": [LONG(n) for n in nums]}


def B(*flags: bool) -> dict[str, object]:
    return {"t": "list", "etype": "bool", "v": [BOOL(flag) for flag in flags]}


def nested(*lists: dict[str, object]) -> dict[str, object]:
    return {"t": "list", "etype": "general", "v": list(lists)}


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("2*3+4", LONG(14)),
        ("1+2*3", LONG(7)),
        ("(2*3)+4", LONG(10)),
        ("neg 2+3", LONG(-5)),
        ("1 2 3+10", L(11, 12, 13)),
        ("1 2 3+10 20 30", L(11, 22, 33)),
        ("2 3*4 5-6 7", L(-4, -6)),
        ("count 1 2 3", LONG(3)),
        ("count 42", LONG(1)),
        ('count "abc"', LONG(3)),
        ("til 4", L(0, 1, 2, 3)),
        ("sum 1 2 3 4", LONG(10)),
        ("sum 1 0N 2", LONG(3)),
        ("sum 7", LONG(7)),
        ("avg 1 2 3", FLOAT(2.0)),
        ("avg 1 0N 3", FLOAT(2.0)),
        ("where 1 0 1 1 0b", L(0, 2, 3)),
        ("where 2 0 1", L(0, 0, 2)),
        ("asc 3 1 2", L(1, 2, 3)),
        ("desc 1 3 2", L(3, 2, 1)),
        ("distinct 1 2 1 3 2", L(1, 2, 3)),
        ("reverse 1 2 3", L(3, 2, 1)),
        ("(1 2 3)[1]", LONG(2)),
        ("(1 2 3)[5]", NULL_LONG),
        ("(1 2 3)[0 2]", L(1, 3)),
        ("2#1 2 3 4", L(1, 2)),
        ("5#1 2", L(1, 2, 1, 2, 1)),
        ("-2#1 2 3 4", L(3, 4)),
        ("1_1 2 3 4", L(2, 3, 4)),
        ("1 2,3 4", L(1, 2, 3, 4)),
        ("1 2 3?2", LONG(1)),
        ("1 2 3?9", LONG(3)),
        ("0N=0N", BOOL(False)),
        ("0N~0N", BOOL(True)),
        ("null 0N", BOOL(True)),
        ("null 1", BOOL(False)),
        ("not 0 1 2", B(True, False, False)),
        ("$[1b;10;20]", LONG(10)),
        ("$[0b;10;20]", LONG(20)),
        ("{x+y}[2;3]", LONG(5)),
        ("{[a;b] a*b}[4;5]", LONG(20)),
        ("{x*x} 7", LONG(49)),
        ("1 2 3+'10 20 30", L(11, 22, 33)),
        ("(+/)1 2 3 4", LONG(10)),
        ("(+\\)1 2 3 4", L(1, 3, 6, 10)),
        ("(-':)1 4 9", L(1, 3, 5)),
        ("type 42", {"t": "short", "v": -7}),
        ("1%2", FLOAT(0.5)),
        ("1%0", {"t": "float", "v": "inf"}),
        ("0%0", NULL_FLOAT),
        ("min 3 0N 1", LONG(1)),
        ("max 3 0N 1", LONG(3)),
        ("enlist 1", L(1)),
        ("raze (1 2;3 4)", L(1, 2, 3, 4)),
        ("first 1 2 3", LONG(1)),
        ("last 1 2 3", LONG(3)),
        ("0^0N 1 0N", L(0, 1, 0)),
        ("1 2 3=1 2 4", B(True, True, False)),
        ("2<>2", BOOL(False)),
        ("2<=2", BOOL(True)),
        ("sqrt 9", FLOAT(3.0)),
        ("abs -5", LONG(5)),
        ('"abc"[1]', {"t": "char", "v": "b"}),
        ("`abc=`abc", BOOL(True)),
        ("`abc=`def", BOOL(False)),
        ("2 2 3 in 1 2", B(True, True, False)),
        ("1~1f", BOOL(False)),
        ("1 2~1 2", BOOL(True)),
        ("sums 1 2 3", L(1, 3, 6)),
        ("sums 2 0N 4", L(2, 2, 6)),
        ("2020.01.01+2", {"t": "date", "v": "2020-01-03"}),
        ("first 0#1 2 3", NULL_LONG),
        ("0#1 2 3", {"t": "list", "etype": "long", "v": []}),
        ("9223372036854775807+1", LONG(-9223372036854775808)),
        ("1 2+\\:10 20 30", nested(L(11, 21, 31), L(12, 22, 32))),
        ("1 2 3+/:10 20", nested(L(11, 12, 13), L(21, 22, 23))),
        ("1 2 3 + each 10 20 30", L(11, 22, 33)),
        ("$[0b;10;1b;20;30]", LONG(20)),
        ("/ comment\n1+2", LONG(3)),
        ("a:1 2 3\nb:10\na+b", L(11, 12, 13)),
        ("f:{x+y}\ng:f[10]\ng 5", LONG(15)),
        ("a:100\nf:{[a] {a+x}}\nf[3] 10", LONG(110)),
        ("{[x] :x+1; x+9}[3]", LONG(4)),
        ("string `abc", {"t": "list", "etype": "char", "v": [{"t": "char", "v": "a"}, {"t": "char", "v": "b"}, {"t": "char", "v": "c"}]}),
    ],
)
def test_value(source: str, expected: dict[str, object]) -> None:
    result = validate(source, expected)
    assert result.matched, (source, result.display, result.canon, result.signal, result.translation.python, result.diagnostics)


def test_length_signal() -> None:
    result = validate("1 2+1 2 3", expected_signal="length")
    assert result.matched, (result.signal, result.diagnostics, result.translation.python)


def test_dict_and_tables() -> None:
    dict_case = validate("(`a`b!1 2)+10")
    assert dict_case.matched is None
    assert dict_case.canon == {
        "t": "dict",
        "keys": [{"t": "symbol", "v": "a"}, {"t": "symbol", "v": "b"}],
        "vals": [LONG(11), LONG(12)],
    }, dict_case.canon
    selected = validate("t:([] a:1 2 3; b:10 20 30)\nselect a from t where a>1")
    assert selected.canon == {
        "t": "table",
        "keys": [],
        "cols": ["a"],
        "types": {"a": "long"},
        "rows": [{"a": LONG(2)}, {"a": LONG(3)}],
    }, (selected.canon, selected.signal, selected.translation.python)
    added = validate("t:([] a:1 2 3; b:10 20 30)\nselect s:a+b from t")
    assert added.canon["rows"] == [{"s": LONG(11)}, {"s": LONG(22)}, {"s": LONG(33)}], added.canon
    agg = validate("t:([] a:1 2 3)\nselect sum a from t")
    assert agg.canon["rows"] == [{"a": LONG(6)}], (agg.canon, agg.signal, agg.translation.python)
    executed = validate("t:([] a:1 2 3; b:10 20 30)\nexec b from t where a<3")
    assert executed.canon == L(10, 20), (executed.canon, executed.signal, executed.translation.python)
    updated = validate("t:([] a:1 2; b:10 20)\nupdate c:a+b from t")
    assert [row["c"] for row in updated.canon["rows"]] == [LONG(11), LONG(22)], updated.canon
    deleted = validate("t:([] a:1 2 3)\ndelete from t where a=2")
    assert [row["a"]["v"] for row in deleted.canon["rows"]] == [1, 3], deleted.canon
    grouped = validate("t:([] b:`x`y`x; a:1 2 3)\nselect sum a by b from t")
    assert grouped.canon["keys"] == ["b"], grouped.canon
    assert grouped.canon["rows"] == [
        {"b": {"t": "symbol", "v": "x"}, "a": LONG(4)},
        {"b": {"t": "symbol", "v": "y"}, "a": LONG(2)},
    ], (grouped.canon, grouped.signal, grouped.translation.python)
    extended = validate("([] s:`a`b`c; p:10)")
    assert [row["p"]["v"] for row in extended.canon["rows"]] == [10, 10, 10], extended.canon
    counted = validate("t:([] a:1 2 3)\ncount t")
    assert counted.canon == LONG(3)


def test_date_object_roundtrip() -> None:
    assert dt.date(2020, 1, 3).isoformat() == "2020-01-03"
