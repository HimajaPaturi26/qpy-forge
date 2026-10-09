"""Cartesian cross.

Each left item is paired with each right item, left item first.
An atom counts as one item. A table is not a list of items.
These expectations were not copied from the translator.
"""

from q2py.pipeline import translate, validate

LONG = lambda n: {"t": "long", "v": n}  # noqa: E731


def pair(*items: dict[str, object]) -> dict[str, object]:
    etype = "long"
    if any(item.get("t") != "long" for item in items):
        etype = "general"
    return {"t": "list", "etype": etype, "v": list(items)}


def pairs(*rows: dict[str, object]) -> dict[str, object]:
    return {"t": "list", "etype": "general", "v": list(rows)}


def test_cross_pairs_each_left_with_each_right() -> None:
    result = validate(
        "1 2 cross 3 4",
        pairs(pair(LONG(1), LONG(3)), pair(LONG(1), LONG(4)), pair(LONG(2), LONG(3)), pair(LONG(2), LONG(4))),
    )
    assert result.matched, result.canon
    atom = validate("1 cross 2 3", pairs(pair(LONG(1), LONG(2)), pair(LONG(1), LONG(3))))
    assert atom.matched, atom.canon
    symbol = {"t": "symbol", "v": "a"}
    mixed = validate("1 2 cross `a", pairs(pair(LONG(1), symbol), pair(LONG(2), symbol)))
    assert mixed.matched, mixed.canon


def test_cross_is_right_to_left_and_empty_is_empty() -> None:
    inner = pair(LONG(2), LONG(3))
    outer = {"t": "list", "etype": "general", "v": [LONG(1), inner]}
    nested = validate("1 cross 2 cross 3", pairs(outer))
    assert nested.matched, nested.canon
    empty = validate("() cross 1 2", {"t": "list", "etype": "general", "v": []})
    assert empty.matched, empty.canon
    assert validate("1 2 cross ()", {"t": "list", "etype": "general", "v": []}).matched


def test_cross_rejects_a_table_and_a_prefix() -> None:
    typed = validate("1 cross ([] a:1 2)", expected_signal="type")
    assert typed.matched and typed.signal == "type"
    translated = translate("1 2 cross 3 4")
    assert translated.support == "supported"
    assert "q.q_cross" in translated.python
    prefix = translate("cross 1 2")
    assert prefix.support == "unsupported"
    assert prefix.python == ""
