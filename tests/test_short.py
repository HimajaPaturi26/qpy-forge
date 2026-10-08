"""Short literals wrap at 16 bits and promote against a long."""

from q2py.pipeline import translate, validate

SHORT = lambda n: {"t": "short", "v": n}  # noqa: E731
LONG = lambda n: {"t": "long", "v": n}  # noqa: E731


def test_short_plus_short_stays_short() -> None:
    result = validate("1h+2h", SHORT(3))
    assert result.matched, (result.canon, result.signal)
    assert result.translation.support == "partial"


def test_short_wraps_at_16_bits() -> None:
    result = validate("32767h+1h", SHORT(-32768))
    assert result.matched, (result.canon, result.signal)


def test_short_plus_long_promotes() -> None:
    result = validate("1h+1", LONG(2))
    assert result.matched, (result.canon, result.signal)


def test_glued_i_is_the_int_suffix() -> None:
    result = validate("1i+2i", {"t": "int", "v": 3})
    assert result.matched, (result.canon, result.signal, result.translation.features)
    assert result.translation.support == "partial"
    assert "literal-int" in result.translation.features
    spaced = translate("1 i")
    assert "literal-int" not in spaced.features
    assert "virtual-i" in spaced.features
