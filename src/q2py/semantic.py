"""Semantic analysis: lower the AST, infer query names, and classify support."""

from __future__ import annotations

from dataclasses import dataclass, field

from q2py.astnodes import (
    Apply,
    Assign,
    Binary,
    Cond,
    Empty,
    Lambda,
    ListLit,
    Lit,
    Name,
    Node,
    Query,
    Return,
    Script,
    Strand,
    TableLit,
    Unary,
    UnsupportedNode,
    Verb,
)
from q2py.diagnostics import Diagnostic, partial, unsupported
from q2py.ir import (
    IR,
    App,
    Bin,
    Const,
    Hole,
    IfCond,
    Lam,
    Lst,
    Qry,
    Refused,
    Ret,
    Seq,
    Set,
    Tbl,
    Un,
    Var,
    VerbRef,
)
from q2py.support import PARTIAL_FEATURES, PARTIAL_NOTES

_LITERAL_FEATURE = {
    "long": "literal-long",
    "float": "literal-float",
    "bool": "literal-bool",
    "char": "literal-char",
    "symbol": "literal-symbol",
    "date": "literal-date",
    "short": "literal-short",
    "int": "literal-int",
    "byte": "literal-byte",
    "real": "literal-real",
    "month": "literal-month",
    "timestamp": "literal-timestamp",
}

_PARTIAL_OPS = {"div-int": "div-int", "mod": "mod"}


@dataclass
class SemanticResult:
    ir: Seq
    features: list[str] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def support(self) -> str:
        if any(item.support == "unsupported" for item in self.diagnostics):
            return "unsupported"
        if any(item.support == "partial" for item in self.diagnostics):
            return "partial"
        return "supported"


def analyze(script: Script, diagnostics: list[Diagnostic] | None = None) -> SemanticResult:
    features: list[str] = []
    diags = list(diagnostics or [])
    seq = _lower_script(script, features, diags)
    return SemanticResult(seq, _unique(features), diags)


def _lower_script(script: Script, features: list[str], diags: list[Diagnostic]) -> Seq:
    return Seq(script.line, script.col, [_lower(stmt, features, diags) for stmt in script.stmts])


def _lower(node: Node, features: list[str], diags: list[Diagnostic]) -> IR:
    if isinstance(node, Lit):
        feature = _LITERAL_FEATURE.get(node.typ, "literal-long")
        if node.null:
            features.append("literal-null")
        features.append(feature)
        _note_partial(feature, node, diags)
        return Const(node.line, node.col, node.typ, node.value, node.null)
    if isinstance(node, Name):
        if node.name == "i":
            features.append("virtual-i")
        return Var(node.line, node.col, node.name)
    if isinstance(node, Strand):
        features.append("strand")
        return Lst(node.line, node.col, [_lower(item, features, diags) for item in node.items], "infer")
    if isinstance(node, ListLit):
        features.append("list")
        return Lst(node.line, node.col, [_lower(item, features, diags) for item in node.items], node.etype)
    if isinstance(node, Empty):
        features.append("literal-null")
        return Const(node.line, node.col, "long", None, True)
    if isinstance(node, Unary):
        _feature_op(node.op, node.adverb, features, diags, node)
        return Un(node.line, node.col, node.op, node.adverb, _lower(node.arg, features, diags))
    if isinstance(node, Binary):
        _feature_op(node.op, node.adverb, features, diags, node)
        if node.adverb == "over" and _is_unary_lambda(node.left):
            features.append("converge")
            _note_partial("converge", node, diags)
        return Bin(
            node.line,
            node.col,
            node.op,
            node.adverb,
            _lower(node.left, features, diags),
            _lower(node.right, features, diags),
        )
    if isinstance(node, Apply):
        features.append("projection" if _has_hole(node) else "apply")
        return App(
            node.line,
            node.col,
            _lower(node.fn, features, diags),
            [_lower_arg(arg, features, diags) for arg in node.args],
        )
    if isinstance(node, Verb):
        _feature_op(node.op, node.adverb, features, diags, node)
        return VerbRef(node.line, node.col, node.op, node.adverb)
    if isinstance(node, Lambda):
        features.append("lambda")
        return Lam(node.line, node.col, list(node.params), [_lower(stmt, features, diags) for stmt in node.body])
    if isinstance(node, Assign):
        features.append("assign")
        return Set(node.line, node.col, node.name, _lower(node.expr, features, diags), node.global_)
    if isinstance(node, Return):
        return Ret(node.line, node.col, _lower(node.expr, features, diags))
    if isinstance(node, Cond):
        features.append("cond")
        return IfCond(node.line, node.col, [_lower(arg, features, diags) for arg in node.args])
    if isinstance(node, TableLit):
        features.append("keyed-table" if node.keys else "table")
        return Tbl(
            node.line,
            node.col,
            [(name, _lower(expr, features, diags)) for name, expr in node.keys],
            [(name, _lower(expr, features, diags)) for name, expr in node.cols],
        )
    if isinstance(node, Query):
        features.append(node.kind)
        if node.by:
            features.append("by")
        cols = [(_infer_name(expr, explicit), _lower(expr, features, diags)) for explicit, expr in node.cols]
        by = [(_infer_name(expr, explicit), _lower(expr, features, diags)) for explicit, expr in node.by]
        table = _lower(node.table, features, diags) if node.table is not None else Refused(node.line, node.col, "missing table")
        where = _lower(node.where, features, diags) if node.where is not None else None
        return Qry(node.line, node.col, node.kind, cols, table, where, by, list(node.drop_cols))
    if isinstance(node, UnsupportedNode):
        diags.append(unsupported("semantic", node.message, node.line, node.col))
        return Refused(node.line, node.col, node.message)
    if isinstance(node, Script):
        features.append("script")
        return _lower_script(node, features, diags)
    diags.append(unsupported("semantic", f"unhandled syntax {type(node).__name__}", getattr(node, "line", 1), getattr(node, "col", 1)))
    return Refused(getattr(node, "line", 1), getattr(node, "col", 1), type(node).__name__)


def _lower_arg(node: Node, features: list[str], diags: list[Diagnostic]) -> IR:
    if isinstance(node, Empty):
        return Hole(node.line, node.col)
    return _lower(node, features, diags)


def _feature_op(op: str, adverb: str | None, features: list[str], diags: list[Diagnostic], node: Node) -> None:
    if op in {"add", "sub", "mul", "div"}:
        features.append("infix-arith")
    elif op in {"eq", "ne", "lt", "gt", "le", "ge"}:
        features.append("infix-compare")
    elif op == "match":
        features.append("match")
    elif op in {"fill", "join", "take", "drop", "find", "in", "dict"}:
        features.append({"fill": "fill", "join": "join", "take": "take", "drop": "drop", "find": "find", "in": "in", "dict": "dict"}[op])
    elif op in _PARTIAL_OPS:
        features.append(_PARTIAL_OPS[op])
        _note_partial(_PARTIAL_OPS[op], node, diags)
    elif op in {"or", "and", "dot", "cast"}:
        diags.append(unsupported("semantic", f"verb {op} is outside the supported subset", node.line, node.col))
    else:
        features.append(op if op in {"til", "count", "sum", "sums", "avg", "min", "max", "first", "last", "reverse", "asc", "desc", "distinct", "where", "enlist", "raze", "abs", "sqrt", "type", "string", "flip", "neg", "not", "null"} else "prefix")
        if op not in {"til", "count", "sum", "sums", "avg", "min", "max", "first", "last", "reverse", "asc", "desc", "distinct", "where", "enlist", "raze", "abs", "sqrt", "type", "string", "flip", "neg", "not", "null", "sub"}:
            diags.append(unsupported("semantic", f"verb {op} is outside the supported subset", node.line, node.col))
    if adverb:
        features.append(adverb)


def _note_partial(feature: str, node: Node, diags: list[Diagnostic]) -> None:
    if feature in PARTIAL_FEATURES:
        diags.append(partial("semantic", PARTIAL_NOTES.get(feature, feature), node.line, node.col))


def _infer_name(expr: Node, explicit: str | None) -> str:
    if explicit:
        return explicit
    found = _first_name(expr)
    return found or "x"


def _first_name(node: Node) -> str | None:
    if isinstance(node, Name):
        return node.name
    for child in _children(node):
        found = _first_name(child)
        if found:
            return found
    return None


def _children(node: Node) -> list[Node]:
    if isinstance(node, (Unary, Return)):
        return [node.arg] if isinstance(node, Unary) else [node.expr]
    if isinstance(node, Binary):
        return [node.left, node.right]
    if isinstance(node, Apply):
        return [node.fn, *node.args]
    if isinstance(node, (Strand, ListLit)):
        return list(node.items)
    if isinstance(node, Cond):
        return list(node.args)
    if isinstance(node, Lambda):
        return list(node.body)
    if isinstance(node, Assign):
        return [node.expr]
    return []


def _has_hole(node: Apply) -> bool:
    return any(isinstance(arg, Empty) for arg in node.args)


def _is_unary_lambda(node: Node) -> bool:
    return isinstance(node, Lambda) and len(node.params) <= 1


def _unique(items: list[str]) -> list[str]:
    seen: list[str] = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen
