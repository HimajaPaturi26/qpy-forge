"""Structured diagnostics. A refusal is a result, not an exception to hide."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Diagnostic:
    code: str
    stage: str
    severity: str
    support: str
    message: str
    line: int = 1
    col: int = 1

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def unsupported(stage: str, message: str, line: int = 1, col: int = 1, code: str = "Q2PY300") -> Diagnostic:
    return Diagnostic(
        code=code,
        stage=stage,
        severity="error",
        support="unsupported",
        message=message,
        line=line,
        col=col,
    )


def partial(stage: str, message: str, line: int = 1, col: int = 1, code: str = "Q2PY310") -> Diagnostic:
    return Diagnostic(
        code=code,
        stage=stage,
        severity="warning",
        support="partial",
        message=message,
        line=line,
        col=col,
    )


def error(stage: str, message: str, line: int = 1, col: int = 1, code: str = "Q2PY200") -> Diagnostic:
    return Diagnostic(
        code=code,
        stage=stage,
        severity="error",
        support="supported",
        message=message,
        line=line,
        col=col,
    )
