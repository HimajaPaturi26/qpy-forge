"""Lower IR to readable Python that calls q2py.runtime."""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, field

from q2py.ir import (
    IR,
    App,
    Bin,
    Const,
    Hole,
    IfCond,
    Iter,
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

_BIN = {
    "add": "add",
    "sub": "sub",
    "mul": "mul",
    "div": "div",
    "eq": "eq",
    "ne": "ne",
    "lt": "lt",
    "gt": "gt",
    "le": "le",
    "ge": "ge",
    "match": "match",
    "fill": "q_fill",
    "join": "q_join",
    "take": "q_take",
    "drop": "q_drop",
    "find": "q_find",
    "dict": "q_dict",
    "in": "q_in",
    "div-int": "q_div",
    "mod": "q_mod",
    "or": "q_or",
    "and": "q_and",
    "cast": "q_cast",
    "xbar": "q_xbar",
    "rotate": "q_rotate",
    "except": "q_except",
    "inter": "q_inter",
    "union": "q_union",
    "cross": "q_cross",
}

_UNARY = {
    "neg": "q_neg",
    "not": "q_not",
    "null": "q_null",
    "til": "q_til",
    "count": "q_count",
    "sum": "q_sum",
    "sums": "q_sums",
    "avg": "q_avg",
    "min": "q_min",
    "max": "q_max",
    "first": "q_first",
    "last": "q_last",
    "reverse": "q_reverse",
    "asc": "q_asc",
    "desc": "q_desc",
    "distinct": "q_distinct",
    "where": "q_where",
    "enlist": "q_enlist",
    "raze": "q_raze",
    "abs": "q_abs",
    "sqrt": "q_sqrt",
    "type": "q_type",
    "string": "q_string",
    "flip": "q_flip",
    "prd": "q_prd",
    "prds": "q_prds",
    "all": "q_all",
    "any": "q_any",
    "mins": "q_mins",
    "maxs": "q_maxs",
    "iasc": "q_iasc",
    "idesc": "q_idesc",
    "floor": "q_floor",
    "ceiling": "q_ceiling",
    "signum": "q_signum",
    "prev": "q_prev",
    "next": "q_next",
    "fills": "q_fills",
    "med": "q_med",
    "var": "q_var",
    "dev": "q_dev",
    "differ": "q_differ",
    "group": "q_group",
    "cols": "q_cols",
    "key": "q_key",
    "value": "q_value",
    "sub": "q_neg",
}


@dataclass
class Generated:
    source: str
    maps: list[dict[str, int]] = field(default_factory=list)
    refused: str | None = None


def generate(seq: Seq) -> Generated:
    gen = _Gen()
    body = gen.sequence(seq, "env", set(), indent=1)
    source = "\n".join(
        [
            "import q2py.runtime as q",
            "",
            "def q2py_program():",
            "    env = q.Env()",
            *body,
            "",
        ]
    )
    return Generated(source + "\n", gen.maps, gen.refused)


class _Gen:
    def __init__(self) -> None:
        self.maps: list[dict[str, int]] = []
        self.refused: str | None = None
        self.counter = 0
        self.hoist: list[str] = []

    def fresh(self, prefix: str) -> str:
        self.counter += 1
        return f"_{prefix}{self.counter}"

    def sequence(self, seq: Seq, env: str, locals_: set[str], indent: int) -> list[str]:
        lines: list[str] = []
        last: str | None = None
        for stmt in seq.stmts:
            if isinstance(stmt, Set):
                lines.extend(self._pad(self.assign(stmt, env, locals_), indent))
                last = None
                continue
            if isinstance(stmt, Ret):
                expr = self.expr(stmt.expr, env, locals_)
                lines.append(self._line(f"return {expr}", indent))
                self.maps.append({"python_line": 0, "q_line": stmt.line, "q_col": stmt.col})
                return lines
            produced = self.expr(stmt, env, locals_)
            name = self.fresh("v")
            lines.extend(self._pad(self.hoist, indent))
            self.hoist = []
            lines.append(self._line(f"{name} = {produced}", indent))
            self.maps.append({"python_line": 0, "q_line": stmt.line, "q_col": stmt.col})
            last = name
        if last is None:
            lines.append(self._line("return q.null('long')", indent))
        else:
            lines.append(self._line(f"return {last}", indent))
        return lines

    def assign(self, stmt: Set, env: str, locals_: set[str]) -> list[str]:
        lines = list(self.hoist)
        self.hoist = []
        produced = self.expr(stmt.expr, env, locals_)
        lines.extend(self.hoist)
        self.hoist = []
        if stmt.global_:
            lines.append(f"{env}.set_global({stmt.name!r}, {produced})")
        elif stmt.name in locals_:
            lines.append(f"{stmt.name} = {produced}")
        else:
            lines.append(f"{env}.set({stmt.name!r}, {produced})")
        return lines

    def expr(self, node: IR, env: str, locals_: set[str]) -> str:
        if isinstance(node, Const):
            return self.const(node)
        if isinstance(node, Var):
            if node.name in locals_:
                return node.name
            return f"{env}.get({node.name!r})"
        if isinstance(node, Hole):
            return "q.hole()"
        if isinstance(node, Lst):
            inner = ", ".join(self.expr(item, env, locals_) for item in node.items)
            if not node.items and node.etype not in {"general", "infer"}:
                return f"q.empty({node.etype!r})"
            return f"q.make_list([{inner}])"
        if isinstance(node, Un):
            arg = self.expr(node.arg, env, locals_)
            if node.adverb:
                return f"q.call(q.derived({node.op!r}, {node.adverb!r}), [{arg}], {env})"
            fn = _UNARY.get(node.op)
            if fn is None:
                self.refused = node.op
                return "q.null('long')"
            return f"q.{fn}({arg})"
        if isinstance(node, Bin):
            left = self.expr(node.left, env, locals_)
            right = self.expr(node.right, env, locals_)
            if node.adverb:
                return f"q.call(q.derived({node.op!r}, {node.adverb!r}), [{left}, {right}], {env})"
            fn = _BIN.get(node.op)
            if fn is None:
                self.refused = node.op
                return "q.null('long')"
            return f"q.{fn}({left}, {right})"
        if isinstance(node, Iter):
            fn = self.expr(node.fn, env, locals_)
            return f"q.iterate({fn}, {node.adverb!r})"
        if isinstance(node, VerbRef):
            if node.adverb:
                return f"q.derived({node.op!r}, {node.adverb!r})"
            return f"q.verb({node.op!r})"
        if isinstance(node, App):
            fn = self.expr(node.fn, env, locals_)
            args = ", ".join(self.expr(arg, env, locals_) for arg in node.args)
            return f"q.call({fn}, [{args}], {env})"
        if isinstance(node, Lam):
            return self.lambda_(node, env)
        if isinstance(node, IfCond):
            return self.cond(node, env, locals_)
        if isinstance(node, Tbl):
            return self.table(node, env, locals_)
        if isinstance(node, Qry):
            return self.query(node, env, locals_)
        if isinstance(node, Refused):
            self.refused = node.message or "refused"
            return "q.null('long')"
        self.refused = type(node).__name__
        return "q.null('long')"

    def lambda_(self, node: Lam, env: str) -> str:
        fname = self.fresh("lam")
        assigned = {stmt.name for stmt in node.body if isinstance(stmt, Set) and not stmt.global_}
        locals_ = set(node.params) | assigned
        unpack = [f"{name} = args[{index}]" for index, name in enumerate(node.params)]
        body = self.sequence(Seq(node.line, node.col, node.body), env, locals_, indent=0)
        # sequence at indent 0 still... I used indent 0 which pads 0. But sequence's
        # _line with indent 0 has no pad. Good for the inner list; we reindent here.
        inner = [*unpack, *[line for line in body]]
        definition = [f"def {fname}({env}, args):", *[self._line(line, 1) for line in inner]]
        self.hoist.extend(definition)
        params = "(" + ", ".join(repr(name) for name in node.params) + ")"
        return f"q.lambda_({params}, {fname})"

    def const(self, node: Const) -> str:
        if node.null:
            return f"q.null({node.typ!r})"
        if node.typ == "long" and isinstance(node.value, int):
            return f"q.long({node.value})"
        if node.typ == "short" and isinstance(node.value, int):
            return f"q.short({node.value})"
        if node.typ == "int" and isinstance(node.value, int):
            return f"q.int_({node.value})"
        if node.typ == "byte" and isinstance(node.value, int):
            return f"q.byte({node.value})"
        if node.typ in {"float", "real"} and isinstance(node.value, float):
            if math.isinf(node.value):
                # Python's repr of infinity is the name `inf`, which is not a literal.
                literal = "1e309" if node.value > 0 else "-1e309"
                return f"q.float_({literal})"
            if math.isnan(node.value):
                return "q.null('float')"
            return f"q.float_({node.value!r})"
        if node.typ == "bool":
            return f"q.boolean({bool(node.value)})"
        if node.typ == "char" and isinstance(node.value, str):
            return f"q.char({node.value!r})"
        if node.typ == "symbol":
            return f"q.symbol({str(node.value)!r})"
        if node.typ == "date" and isinstance(node.value, dt.date):
            return f"q.date({node.value.year}, {node.value.month}, {node.value.day})"
        if node.typ == "timestamp" and isinstance(node.value, dt.datetime):
            value = node.value
            return (
                "q.timestamp("
                f"{value.year}, {value.month}, {value.day}, {value.hour}, "
                f"{value.minute}, {value.second}, {value.microsecond})"
            )
        if node.typ == "month" and isinstance(node.value, tuple):
            return f"q.month({int(node.value[0])}, {int(node.value[1])})"
        self.refused = node.typ
        return "q.null('long')"

    def cond(self, node: IfCond, env: str, locals_: set[str]) -> str:
        pairs: list[str] = []
        index = 0
        while index + 1 < len(node.args) - 1:
            test = self.expr(node.args[index], env, locals_)
            result = self.expr(node.args[index + 1], env, locals_)
            pairs.append(f"(lambda: {test}, lambda: {result})")
            index += 2
        other = self.expr(node.args[-1], env, locals_)
        return f"q.q_cond([{', '.join(pairs)}], lambda: {other})"

    def table(self, node: Tbl, env: str, locals_: set[str]) -> str:
        pairs = [(name, self.expr(expr, env, locals_)) for name, expr in [*node.keys, *node.cols]]
        rendered = ", ".join(f"({name!r}, {expr})" for name, expr in pairs)
        keys = ", ".join(repr(name) for name, _ in node.keys)
        return f"q.make_table([{rendered}], [{keys}])"

    def query(self, node: Qry, env: str, locals_: set[str]) -> str:
        table = self.expr(node.table, env, locals_)
        cols = ", ".join(
            f"({name!r}, {self._scope_fn(expr, env, locals_)})" for name, expr in node.cols
        )
        where = self._scope_fn(node.where, env, locals_) if node.where is not None else "None"
        by = ", ".join(f"({name!r}, {self._scope_fn(expr, env, locals_)})" for name, expr in node.by)
        by_arg = f"[{by}]" if node.by else "None"
        if node.kind == "select":
            return f"q.q_select({table}, [{cols}], {where}, {by_arg}, {env})"
        if node.kind == "exec":
            return f"q.q_exec({table}, [{cols}], {where}, {env})"
        if node.kind == "update":
            return f"q.q_update({table}, [{cols}], {where}, {env})"
        drops = ", ".join(repr(name) for name in node.drop_cols)
        return f"q.q_delete({table}, [{drops}], {where}, {env})"

    def _scope_fn(self, node: IR, env: str, locals_: set[str]) -> str:
        rendered = self.expr(node, "scope", locals_)
        return f"(lambda scope: {rendered})"

    def _line(self, text: str, indent: int) -> str:
        return ("    " * indent) + text

    def _pad(self, lines: list[str], indent: int) -> list[str]:
        return [self._line(line, indent) if line else line for line in lines]
