"""Month literals plus integer offsets.

2000.12m+1 rolls to 2001.01m. 2000.01m-1 rolls to 1999.12m.
2001.03m-2000.01m is 14 months. A float offset is a type error.
"""

from q2py.pipeline import translate, validate

MONTH = lambda text: {"t": "month", "v": text}  # noqa: E731
LONG = lambda n: {"t": "long", "v": n}  # noqa: E731


def test_month_add_rolls_the_year() -> None:
    result = validate("2000.12m+1", MONTH("2001-01"))
    assert result.matched, (result.canon, result.signal, result.translation.support)
    assert result.translation.support == "supported"


def test_month_sub_rolls_backward() -> None:
    result = validate("2000.01m-1", MONTH("1999-12"))
    assert result.matched, result.canon


def test_month_difference_is_a_long() -> None:
    result = validate("2001.03m-2000.01m", LONG(14))
    assert result.matched, result.canon


def test_int_plus_month_and_a_vector() -> None:
    added = validate("1+2000.01m", MONTH("2000-02"))
    assert added.matched, added.canon
    vector = validate("2000.01m+1 2")
    assert vector.canon == {
        "t": "list",
        "etype": "month",
        "v": [MONTH("2000-02"), MONTH("2000-03")],
    }, vector.canon


def test_month_plus_float_is_a_type_error() -> None:
    result = validate("2000.01m+1.5", expected_signal="type")
    assert result.matched is True
    assert result.signal == "type"
    assert result.translation.python != ""


def test_timestamp_literal_stays_partial() -> None:
    result = translate("2020.01.01D00:00:00")
    assert result.support == "partial"
    assert result.python != ""
