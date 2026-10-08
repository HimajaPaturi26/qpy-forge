"""Floor division, floor modulo, and capped converge.

Expectations are the integer identities x = (x div y) * y + (x mod y),
and a fixed point of a unary lambda. They were not copied from the translator.
"""

import pytest

from q2py.pipeline import translate, validate

LONG = lambda n: {"t": "long", "v": n}  # noqa: E731


def L(*nums: int) -> dict[str, object]:
    return {"t": "list", "etype": "long", "v": [{"t": "long", "v": n} for n in nums]}


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("7 div 3", LONG(2)),
        ("-7 div 3", LONG(-3)),
        ("7 div -3", LONG(-3)),
        ("-7 div -3", LONG(2)),
        ("-5 div 2", LONG(-3)),
        ("-5 -4 div 2", L(-3, -2)),
        ("7 mod 3", LONG(1)),
        ("-7 mod 3", LONG(2)),
        ("7 mod -3", LONG(-2)),
        ("-7 mod -3", LONG(-1)),
        ("{x}/4", LONG(4)),
        ("{x-x}/1", LONG(0)),
    ],
)
def test_floor_div_mod_and_fixed_point(source: str, expected: dict[str, object]) -> None:
    result = validate(source, expected)
    assert result.matched, (source, result.canon, result.signal, result.translation.support)


def test_div_zero_is_domain() -> None:
    result = validate("1 div 0", expected_signal="domain")
    assert result.matched is True
    assert result.signal == "domain"
    assert result.translation.python != ""


def test_mod_zero_is_domain() -> None:
    result = validate("1 mod 0", expected_signal="domain")
    assert result.matched is True
    assert result.signal == "domain"


def test_nonconverging_unary_over_signals_limit() -> None:
    result = translate("{neg x}/1")
    assert result.support == "partial"
    assert result.python != ""
    ran = validate("{neg x}/1", expected_signal="limit")
    assert ran.matched is True
    assert ran.signal == "limit"


def test_dot_and_cast_still_refused() -> None:
    for source in (". 1", '"i"$10'):
        result = translate(source)
        assert result.support == "unsupported", source
        assert result.python == ""
