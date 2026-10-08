"""Greater (|) and lesser (&).

Expectations follow the written rules: nulls sort below non-nulls, booleans
stay boolean, a float widens the result, and there is no precedence.
They were not copied from the translator.
"""

from q2py.pipeline import translate, validate

LONG = lambda n: {"t": "long", "v": n}  # noqa: E731


def test_greater_and_lesser_atoms() -> None:
    assert validate("1|2", LONG(2)).matched
    assert validate("2&3", LONG(2)).matched
    assert validate("-3|-1", LONG(-1)).matched
    assert validate("-3&-1", LONG(-3)).matched
    assert validate("0N|5", LONG(5)).matched
    assert validate("0N&5", {"t": "long", "null": True}).matched
    assert validate("0N|0N", {"t": "long", "null": True}).matched
    assert validate("0N|1.5", {"t": "float", "v": 1.5}).matched
    assert validate("0N&1.5", {"t": "float", "null": True}).matched


def test_bool_stays_bool_and_float_widens() -> None:
    assert validate("0b|1b", {"t": "bool", "v": True}).matched
    assert validate("0b&1b", {"t": "bool", "v": False}).matched
    assert validate("1b|2", LONG(2)).matched
    assert validate("1&2.5", {"t": "float", "v": 1.0}).matched
    assert validate("0w|5", {"t": "float", "v": "inf"}).matched
    assert validate("-0w|5", {"t": "float", "v": 5.0}).matched


def test_vectors_and_right_to_left() -> None:
    paired = validate("1 4|2 3", {"t": "list", "etype": "long", "v": [LONG(2), LONG(4)]})
    assert paired.matched, paired.canon
    assert validate("1|2&0", LONG(1)).matched
    folded = validate("(|/)1 2 3", LONG(3))
    assert folded.matched, (folded.canon, folded.signal, folded.translation.python)
    assert validate("(&/)1 2 3", LONG(1)).matched


def test_signals_and_support() -> None:
    length = validate("1 2|3 4 5", expected_signal="length")
    assert length.matched
    assert length.signal == "length"
    typed = validate("1|`a", expected_signal="type")
    assert typed.matched
    assert typed.signal == "type"
    greater = translate("1|2")
    assert greater.support == "supported"
    assert "q.q_or" in greater.python
    lesser = translate("2&3")
    assert lesser.support == "supported"
    assert "q.q_and" in lesser.python
    for source in ("\"i\"$10", ". 1"):
        refused = translate(source)
        assert refused.support == "unsupported", source
        assert refused.python == ""
