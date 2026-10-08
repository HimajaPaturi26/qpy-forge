"""Concrete syntax tree produced by the parser."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Node:
    line: int = 1
    col: int = 1


@dataclass
class Lit(Node):
    typ: str = "long"
    value: object = None
    null: bool = False


@dataclass
class Name(Node):
    name: str = ""


@dataclass
class Strand(Node):
    items: list[Node] = field(default_factory=list)


@dataclass
class ListLit(Node):
    items: list[Node] = field(default_factory=list)
    etype: str = "general"


@dataclass
class Empty(Node):
    pass


@dataclass
class Unary(Node):
    op: str = ""
    adverb: str | None = None
    arg: Node = field(default_factory=Node)


@dataclass
class Binary(Node):
    op: str = ""
    adverb: str | None = None
    left: Node = field(default_factory=Node)
    right: Node = field(default_factory=Node)


@dataclass
class Apply(Node):
    fn: Node = field(default_factory=Node)
    args: list[Node] = field(default_factory=list)


@dataclass
class Verb(Node):
    op: str = ""
    adverb: str | None = None


@dataclass
class Derived(Node):
    """A lambda (or other value) with a postfix adverb, as in ``({x*y}/)``."""

    fn: Node = field(default_factory=Node)
    adverb: str = ""


@dataclass
class Lambda(Node):
    params: list[str] = field(default_factory=list)
    body: list[Node] = field(default_factory=list)
    explicit_params: bool = False


@dataclass
class Assign(Node):
    name: str = ""
    expr: Node = field(default_factory=Node)
    global_: bool = False


@dataclass
class Return(Node):
    expr: Node = field(default_factory=Node)


@dataclass
class Cond(Node):
    args: list[Node] = field(default_factory=list)


@dataclass
class TableLit(Node):
    keys: list[tuple[str, Node]] = field(default_factory=list)
    cols: list[tuple[str, Node]] = field(default_factory=list)


@dataclass
class Query(Node):
    kind: str = "select"
    cols: list[tuple[str | None, Node]] = field(default_factory=list)
    table: Node | None = None
    where: Node | None = None
    by: list[tuple[str | None, Node]] = field(default_factory=list)
    drop_cols: list[str] = field(default_factory=list)


@dataclass
class UnsupportedNode(Node):
    message: str = ""


@dataclass
class Script(Node):
    stmts: list[Node] = field(default_factory=list)
