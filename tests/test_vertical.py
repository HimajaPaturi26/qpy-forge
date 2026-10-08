from q2py.pipeline import translate, validate


def test_right_to_left_slice() -> None:
    result = validate("2*3+4", {"t": "long", "v": 14})
    assert result.translation.python
    assert result.matched, (result.display, result.canon, result.signal, result.diagnostics, result.translation.python)


def test_unsupported_or_does_not_emit_python() -> None:
    result = translate("1|2")
    assert result.support == "unsupported"
    assert result.python == ""
