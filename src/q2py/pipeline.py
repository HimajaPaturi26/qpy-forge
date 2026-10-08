"""Translate q source through lex, parse, semantic analysis, IR, codegen, and execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from q2py.codegen import generate
from q2py.diagnostics import Diagnostic, error
from q2py.lexer import lex
from q2py.oracle import oracle_status
from q2py.parser import parse
from q2py.sandbox import ExecResult, Executor, SubprocessExecutor
from q2py.semantic import analyze
from q2py.values import canon


@dataclass
class Translation:
    source: str
    support: str
    features: list[str]
    tokens: list[dict[str, Any]]
    python: str
    maps: list[dict[str, int]]
    diagnostics: list[Diagnostic]
    stages: dict[str, str]
    ast: dict[str, Any]
    ir: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "support": self.support,
            "features": self.features,
            "tokens": self.tokens,
            "python": self.python,
            "maps": self.maps,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "stages": self.stages,
            "ast": self.ast,
            "ir": self.ir,
            "oracle": oracle_status(),
        }


@dataclass
class Validation:
    translation: Translation
    executed: bool
    matched: bool | None
    signal: str | None
    display: str
    canon: dict[str, Any] | None
    expected: dict[str, Any] | None
    expected_signal: str | None
    comparison: str
    diagnostics: list[Diagnostic] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = self.translation.to_dict()
        payload.update(
            {
                "executed": self.executed,
                "matched": self.matched,
                "signal": self.signal,
                "display": self.display,
                "canon": self.canon,
                "expected": self.expected,
                "expected_signal": self.expected_signal,
                "comparison": self.comparison,
                "diagnostics": [item.to_dict() for item in self.diagnostics],
            }
        )
        return payload


def translate(source: str) -> Translation:
    stages = {name: "pending" for name in ("lex", "parse", "semantic", "ir", "codegen", "compile")}
    lexed = lex(source)
    stages["lex"] = "error" if any(item.severity == "error" for item in lexed.diagnostics) else "ok"
    parsed = parse(lexed)
    parse_errors = [item for item in parsed.diagnostics if item.severity == "error" and item.stage == "parse"]
    stages["parse"] = "error" if parse_errors else "ok"
    analyzed = analyze(parsed.script, parsed.diagnostics)
    if any(tok.kind == "COMMENT" for tok in lexed.tokens) and "comment" not in analyzed.features:
        analyzed.features.append("comment")
    stages["semantic"] = "error" if analyzed.support == "unsupported" else ("partial" if analyzed.support == "partial" else "ok")
    stages["ir"] = stages["semantic"]
    python = ""
    maps: list[dict[str, int]] = []
    if analyzed.support == "unsupported" or stages["lex"] == "error":
        stages["codegen"] = "skipped"
        stages["compile"] = "skipped"
    else:
        generated = generate(analyzed.ir)
        if generated.refused:
            analyzed.diagnostics.append(error("codegen", f"refused to generate Python for {generated.refused}", code="Q2PY400"))
            stages["codegen"] = "error"
            stages["compile"] = "skipped"
            analyzed = _force_unsupported(analyzed)
        else:
            python = generated.source
            maps = generated.maps
            stages["codegen"] = "ok"
            from q2py.sandbox import validate_generated

            compile_diags = validate_generated(python)
            analyzed.diagnostics.extend(compile_diags)
            stages["compile"] = "error" if compile_diags else "ok"
            if compile_diags:
                python = ""
    return Translation(
        source=source,
        support=analyzed.support if stages["codegen"] != "error" else "unsupported",
        features=analyzed.features,
        tokens=[_token_dict(tok) for tok in lexed.tokens],
        python=python,
        maps=maps,
        diagnostics=analyzed.diagnostics,
        stages=stages,
        ast=_tree(parsed.script),
        ir=_tree(analyzed.ir),
    )


def validate(
    source: str,
    expected: dict[str, Any] | None = None,
    expected_signal: str | None = None,
    executor: Executor | None = None,
) -> Validation:
    translation = translate(source)
    diagnostics = list(translation.diagnostics)
    if translation.support == "unsupported" or not translation.python or translation.stages.get("compile") == "error":
        return Validation(
            translation,
            False,
            False if expected is not None or expected_signal else None,
            None,
            "",
            None,
            expected,
            expected_signal,
            "refused",
            diagnostics,
        )
    runner = executor or SubprocessExecutor()
    result: ExecResult = runner.run(translation.python)
    diagnostics.extend(result.diagnostics)
    translation.stages["exec"] = "ok" if result.ok else "error"
    matched: bool | None
    comparison: str
    if expected_signal:
        matched = result.signal == expected_signal
        comparison = "signal-match" if matched else "signal-mismatch"
    elif expected is not None:
        matched = result.ok and result.canon == expected
        comparison = "value-match" if matched else "value-mismatch"
    else:
        matched = None
        comparison = "executed" if result.ok else "runtime-error"
    translation.stages["compare"] = "skipped" if matched is None else ("ok" if matched else "error")
    return Validation(
        translation,
        result.ok,
        matched,
        result.signal,
        result.display,
        result.canon,
        expected,
        expected_signal,
        comparison,
        diagnostics,
    )


def _force_unsupported(analyzed: Any) -> Any:
    # SemanticResult.support is derived from diagnostics. The codegen error is support=supported
    # unless we record an unsupported diagnostic. Callers that refuse generation pass an
    # unsupported diagnostic before this helper replaces the support label at the translation layer.
    return analyzed


def _token_dict(tok: Any) -> dict[str, Any]:
    return {
        "kind": tok.kind,
        "text": tok.text,
        "line": tok.line,
        "col": tok.col,
        "lit_type": tok.lit_type,
        "null": tok.null,
    }


def _tree(node: Any) -> dict[str, Any]:
    if isinstance(node, (str, int, float, bool)) or node is None:
        return {"v": node}
    if isinstance(node, (list, tuple)):
        return {"list": [_tree(item) for item in node]}
    if hasattr(node, "__dataclass_fields__"):
        data = {"type": type(node).__name__}
        for key, value in asdict(node).items():
            if key in {"line", "col"}:
                data[key] = value
                continue
            data[key] = _jsonish(value)
        return data
    return {"v": str(node)}


def _jsonish(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonish(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonish(item) for key, item in value.items()}
    return str(value)


def canon_json(value: Any) -> dict[str, Any]:
    return canon(value)
