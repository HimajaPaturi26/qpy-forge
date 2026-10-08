"""Numeric $ cast.

Expectations are truncation toward zero, width wrap, and the type characters
b x h i j e f. $[cond;then;else] stays the conditional. These values were
not copied from the translator.
"""

from q2py.pipeline import translate, validate

LONG = lambda n: {"t": "long", "v": n}  # noqa: E731


def test_type_char_and_type_code() -> None:
    assert validate('"j"$1.9', LONG(1)).matched
    assert validate('"j"$-1.9', LONG(-1)).matched
    assert validate('"i"$10', {"t": "int", "v": 10}).matched
    assert validate('"f"$2', {"t": "float", "v": 2.0}).matched
    assert validate('"e"$1', {"t": "real", "v": 1.0}).matched
    assert validate('"b"$2', {"t": "bool", "v": True}).matched
    assert validate('"b"$0', {"t": "bool", "v": False}).matched
    assert validate('"b"$0N', {"t": "bool", "v": False}).matched
    assert validate("7$1.9", LONG(1)).matched
    assert validate('"j"$1+0.5', LONG(1)).matched


def test_wrap_null_and_vector() -> None:
    assert validate('"h"$32768', {"t": "short", "v": -32768}).matched
    assert validate('"x"$256', {"t": "byte", "v": 0}).matched
    assert validate('"x"$-1', {"t": "byte", "v": 255}).matched
    assert validate('"f"$0N', {"t": "float", "null": True}).matched
    paired = validate('"j"$1.2 2.8', {"t": "list", "etype": "long", "v": [LONG(1), LONG(2)]})
    assert paired.matched, paired.canon
    assert validate('"j"$0w', LONG(9223372036854775807)).matched


def test_signals_and_conditional_still_works() -> None:
    typed = validate('"j"$`a', expected_signal="type")
    assert typed.matched and typed.signal == "type"
    domain = validate('"x"$0w', expected_signal="domain")
    assert domain.matched and domain.signal == "domain"
    cond = validate("$[1b;2;3]", LONG(2))
    assert cond.matched, cond.canon
    translated = translate('"i"$10')
    assert translated.support == "supported"
    assert "q.q_cast" in translated.python
    refused = translate("1 2 3 . 0")
    assert refused.support == "unsupported"
    assert refused.python == ""
