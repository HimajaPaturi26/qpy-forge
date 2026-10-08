import pytest

from q2py.pipeline import translate, validate


def test_right_to_left_slice() -> None:
    result = validate("2*3+4", {"t": "long", "v": 14})
    assert result.translation.python
    assert result.matched, (result.display, result.canon, result.signal, result.diagnostics, result.translation.python)


def test_unsupported_or_does_not_emit_python() -> None:
    result = translate("1|2")
    assert result.support == "unsupported"
    assert result.python == ""


@pytest.mark.parametrize("source", ["peach 1 2 3", "if[1b;2]", "do[2;1]", "while[1b;1]", "1?2", "2&3"])
def test_refused_constructs_emit_no_python(source: str) -> None:
    result = translate(source)
    assert result.support == "unsupported", (source, result.support, result.python)
    assert result.python == ""
