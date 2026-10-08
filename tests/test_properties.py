from hypothesis import given
from hypothesis import strategies as st

from q2py.runtime import add, long
from q2py.values import Atom


@given(st.integers(-10_000, 10_000), st.integers(-10_000, 10_000))
def test_long_add_is_commutative(left: int, right: int) -> None:
    assert add(long(left), long(right)) == add(long(right), long(left))


@given(st.integers(-1_000_000, 1_000_000))
def test_null_long_absorbs_addition(number: int) -> None:
    result = add(Atom("long", null=True), long(number))
    assert isinstance(result, Atom)
    assert result.null and result.typ == "long"
