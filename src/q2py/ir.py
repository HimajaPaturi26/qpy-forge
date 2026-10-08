"""Intermediate representation accepted by the code generator.

The IR is the parser tree after semantic analysis: column names are resolved,
support features are attached, and refused constructs are explicit nodes.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IR:
    line: int = 1
    col: int = 1


@dataclass
class Const(IR):
    typ: str = "long"
    value: object = None
    null: bool = False


@dataclass
class Var(IR):
    name: str = ""


@dataclass
class Un(IR):
    op: str = ""
    adverb: str | None = None
    arg: IR = field(default_factory=IR)


@dataclass
class Bin(IR):
    op: str = ""
    adverb: str | None = None
    left: IR = field(default_factory=IR)
    right: IR = field(default_factory=IR)


@dataclass
class App(IR):
    fn: IR = field(default_factory=IR)
    args: list[IR] = field(default_factory=list)


@dataclass
class VerbRef(IR):
    op: str = ""
    adverb: str | None = None


@dataclass
class Lam(IR):
    params: list[str] = field(default_factory=list)
    body: list[IR] = field(default_factory=list)


@dataclass
class Set(IR):
    name: str = ""
    expr: IR = field(default_factory=IR)
    global_: bool = False


@dataclass
class Ret(IR):
    expr: IR = field(default_factory=IR)


@dataclass
class IfCond(IR):
    args: list[IR] = field(default_factory=list)


@dataclass
class Lst(IR):
    items: list[IR] = field(default_factory=list)
    etype: str = "general"


@dataclass
class Tbl(IR):
    keys: list[tuple[str, IR]] = field(default_factory=list)
    cols: list[tuple[str, IR]] = field(default_factory=list)


@dataclass
class Qry(IR):
    kind: str = "select"
    cols: list[tuple[str, IR]] = field(default_factory=list)
    table: IR = field(default_factory=IR)
    where: IR | None = None
    by: list[tuple[str, IR]] = field(default_factory=list)
    drop_cols: list[str] = field(default_factory=list)


@dataclass
class Refused(IR):
    message: str = ""


@dataclass
class Hole(IR):
    """Elided argument: projection hole or an omitted index."""


@dataclass
class Seq(IR):
    stmts: list[IR] = field(default_factory=list)
