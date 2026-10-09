"""Infix xexp.

Expectations follow the published calculation exp(y * log x), written out
below. They were not copied from a translator run, and they are not a live
q-oracle result. q's default printer shows 2 xexp 8 as 256f; the formula
value is the float asserted here.
"""

import math

from q2py.pipeline import translate, validate

FLOAT = lambda number: {"t": "float", "v": number}  # noqa: E731
NULL_FLOAT = {"t": "float", "null": True}
INF = {"t": "float", "v": "inf"}


def F(*items: dict[str, object]) -> dict[str, object]:
    return {"t": "list", "etype": "float", "v": list(items)}


def power(base: float, exponent: float) -> float:
    """Published rule: exp(y * log x), with 0 * infinity as a null."""
    log_base = float("-inf") if base == 0.0 else math.log(base)
    if exponent == 0.0 and math.isinf(log_base):
        return float("nan")
    product = exponent * log_base
    if math.isnan(product):
        return float("nan")
    if math.isinf(product):
        return float("inf") if product > 0.0 else 0.0
    return math.exp(product)


# Seven cases for the execution failure that looked up the name xexp.
# The bracket form stays unsupported, matching div and the other infix words.
CLEAR_STRESS: tuple[tuple[str, str, object], ...] = (
    ("2 xexp 8", "value", FLOAT(power(2.0, 8.0))),
    ("2 xexp 3", "value", FLOAT(7.999999999999998)),
    ("-2 xexp 3", "value", NULL_FLOAT),
    ("1 2 3 xexp 2", "value", F(FLOAT(power(1.0, 2.0)), FLOAT(power(2.0, 2.0)), FLOAT(power(3.0, 2.0)))),
    (
        "1.5 xexp -4.2 0 0.1 0n 0w",
        "value",
        F(FLOAT(power(1.5, -4.2)), FLOAT(1.0), FLOAT(power(1.5, 0.1)), NULL_FLOAT, INF),
    ),
    ("1 2 xexp 3 4 5", "signal", "length"),
    ("xexp[2;8]", "unsupported", None),
)


def test_xexp_is_generated_as_a_runtime_call() -> None:
    translated = translate("2 xexp 3")
    assert translated.support == "supported"
    assert translated.stages["compile"] == "ok"
    assert "q.q_xexp" in translated.python
    assert "env.get('xexp')" not in translated.python
    result = validate("2 xexp 3", FLOAT(7.999999999999998))
    assert result.executed
    assert result.matched
    assert result.signal is None
    assert result.comparison == "value-match"


def test_clear_stress_seven() -> None:
    outcomes: list[tuple[str, str]] = []
    for source, kind, expected in CLEAR_STRESS:
        if kind == "unsupported":
            translated = translate(source)
            ok = translated.support == "unsupported" and translated.python == ""
            outcomes.append((source, "unsupported" if ok else "failed"))
            assert ok, (source, translated.support, translated.python, translated.diagnostics)
            continue
        if kind == "signal":
            result = validate(source, expected_signal=str(expected))
            outcomes.append((source, "passed" if result.matched else "failed"))
            assert result.matched, (source, result.signal, result.comparison)
            continue
        result = validate(source, expected)
        outcomes.append((source, "passed" if result.matched else "failed"))
        assert result.matched, (source, result.canon, result.signal, result.translation.python)
    assert [status for _, status in outcomes] == [
        "passed",
        "passed",
        "passed",
        "passed",
        "passed",
        "passed",
        "unsupported",
    ]


def test_xexp_nulls_zero_and_type() -> None:
    assert validate("0n xexp 2", NULL_FLOAT).matched
    assert validate("2 xexp 0n", NULL_FLOAT).matched
    assert validate("0 xexp 0", NULL_FLOAT).matched
    assert validate("0 xexp 2", FLOAT(0.0)).matched
    assert validate("0 xexp -1", INF).matched
    assert validate("2 xexp 0", FLOAT(1.0)).matched
    typed = validate("`a xexp 2", expected_signal="type")
    assert typed.matched and typed.signal == "type"


def test_arithmetic_and_calls_still_run() -> None:
    arithmetic = validate("2*3+4", {"t": "long", "v": 14})
    assert arithmetic.matched and arithmetic.executed
    called = validate("{x+y}[2;3]", {"t": "long", "v": 5})
    assert called.matched and called.executed
    powered = validate("{x xexp y}[2;3]", FLOAT(7.999999999999998))
    assert powered.matched and powered.executed
    # No precedence: the left of * is 2, and the right expression is 3 xexp 2.
    composed = validate("2*3 xexp 2", FLOAT(2.0 * power(3.0, 2.0)))
    assert composed.matched, composed.canon
