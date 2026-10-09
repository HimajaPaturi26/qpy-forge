"""Recursive-descent parser for the documented q subset.

Expressions are right-associative. The left argument of an infix verb is the
noun immediately to its left. Numeric vectors bind before application.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from q2py.astnodes import (
    Apply,
    Assign,
    Binary,
    Cond,
    Derived,
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
from q2py.diagnostics import Diagnostic, error, unsupported
from q2py.lexer import LexResult, Token

_PREFIX = {
    "neg",
    "not",
    "null",
    "til",
    "count",
    "sum",
    "sums",
    "avg",
    "min",
    "max",
    "first",
    "last",
    "reverse",
    "asc",
    "desc",
    "distinct",
    "where",
    "enlist",
    "raze",
    "abs",
    "sqrt",
    "type",
    "string",
    "flip",
    "key",
    "value",
    "cols",
    "prd",
    "prds",
    "all",
    "any",
    "mins",
    "maxs",
    "iasc",
    "idesc",
    "floor",
    "ceiling",
    "signum",
    "prev",
    "next",
    "fills",
    "med",
    "var",
    "dev",
    "differ",
    "group",
}

_INFIX_WORDS = {"div", "mod", "in", "xbar", "rotate", "except", "inter", "union", "cross", "xexp"}

_OP_KIND = {
    "PLUS": "add",
    "MINUS": "sub",
    "STAR": "mul",
    "PERCENT": "div",
    "EQ": "eq",
    "NE": "ne",
    "LT": "lt",
    "GT": "gt",
    "LE": "le",
    "GE": "ge",
    "MATCH": "match",
    "COMMA": "join",
    "TAKE": "take",
    "DROP": "drop",
    "BANG": "dict",
    "QUERY": "find",
    "AT": "apply",
    "DOT": "dot",
    "OR": "or",
    "AND": "and",
    "DOLLAR": "cast",
    "FILL": "fill",
}

_ADVERB = {
    "EACH": "each",
    "EACH_LEFT": "each-left",
    "EACH_RIGHT": "each-right",
    "EACH_PRIOR": "each-prior",
    "OVER": None,  # glyph `/` is tokenized only as part of /: or comment or...
}

# Glyph `/` and `\` that are iterators are single-character tokens PLUS?
# The lexer emits `/` as... I didn't map bare `/`!
# Looking at lexer: if `/` is not a comment, it falls through to _INFIX_GLYPHS?
# `/` is NOT in _INFIX_GLYPHS. `\` is not either.
# I need to handle bare `/` and `\` in the lexer. I'll fix the lexer.
# For now parser expects OVER and SCAN token kinds.


@dataclass
class ParseResult:
    script: Script
    diagnostics: list[Diagnostic] = field(default_factory=list)


def parse(lexed: LexResult) -> ParseResult:
    parser = _Parser(lexed.tokens, list(lexed.diagnostics))
    script = parser.parse_script()
    return ParseResult(script, parser.diagnostics)


class _Parser:
    def __init__(self, tokens: list[Token], diagnostics: list[Diagnostic]) -> None:
        self.tokens = [tok for tok in tokens if tok.kind != "COMMENT"]
        self.diagnostics = diagnostics
        self.i = 0
        self.depth = 0

    def parse_script(self) -> Script:
        stmts: list[Node] = []
        self._skip_sep()
        while not self._eof() and not self._check("RBRACE"):
            stmts.append(self._stmt())
            if not self._skip_sep() and not self._eof() and not self._check("RBRACE"):
                tok = self._peek()
                self.diagnostics.append(error("parse", f"expected separator before {tok.text!r}", tok.line, tok.col))
                break
        return Script(stmts=stmts)

    def _stmt(self) -> Node:
        if self._check("IDENT") and self._assign_ahead():
            return self._assign(False)
        if self._match("COLON"):
            tok = self._prev()
            return Return(tok.line, tok.col, self._expr())
        if self._check_kw("select"):
            return self._query("select")
        if self._check_kw("exec"):
            return self._query("exec")
        if self._check_kw("update"):
            return self._query("update")
        if self._check_kw("delete"):
            return self._query("delete")
        if self._check_kw("if") or self._check_kw("do") or self._check_kw("while") or self._check_kw("peach"):
            tok = self._advance()
            self.diagnostics.append(
                unsupported("parse", f"{tok.text} is outside the supported subset", tok.line, tok.col)
            )
            return UnsupportedNode(tok.line, tok.col, f"{tok.text} is unsupported")
        return self._expr()

    def _assign(self, global_: bool) -> Assign:
        tok = self._advance()
        if self._match("ASSIGN_GLOBAL"):
            global_ = True
        else:
            self._match("COLON")
        return Assign(tok.line, tok.col, tok.text, self._expr(), global_)

    def _assign_ahead(self) -> bool:
        nxt = self._peek_kind(1)
        return nxt in {"COLON", "ASSIGN_GLOBAL"}

    def _query(self, kind: str) -> Node:
        tok = self._advance()
        if kind == "delete" and self._check_kw("from"):
            self._advance()
            table = self._expr()
            where = self._where()
            return Query(tok.line, tok.col, kind, [], table, where, [], [])
        if kind == "delete":
            names: list[str] = []
            while self._check("IDENT") and not self._check_kw("from"):
                names.append(self._advance().text)
                if not self._match("COMMA"):
                    break
            if not self._match_kw("from"):
                self.diagnostics.append(error("parse", "delete requires from", tok.line, tok.col))
                return UnsupportedNode(tok.line, tok.col, "delete")
            table = self._expr()
            where = self._where()
            return Query(tok.line, tok.col, kind, [], table, where, [], names)
        cols = self._col_list(stop_from=True)
        by: list[tuple[str | None, Node]] = []
        if self._match_kw("by"):
            by = self._col_list(stop_from=True)
        if not self._match_kw("from"):
            self.diagnostics.append(error("parse", f"{kind} requires from", tok.line, tok.col))
            return UnsupportedNode(tok.line, tok.col, kind)
        table = self._expr()
        where = self._where()
        return Query(tok.line, tok.col, kind, cols, table, where, by, [])

    def _where(self) -> Node | None:
        if self._match_kw("where"):
            return self._expr()
        return None

    def _col_list(self, stop_from: bool) -> list[tuple[str | None, Node]]:
        cols: list[tuple[str | None, Node]] = []
        if self._at_clause_end():
            return cols
        while not self._eof() and not self._at_clause_end():
            cols.append(self._column())
            if not self._match("COMMA"):
                break
        return cols

    def _at_clause_end(self) -> bool:
        return (
            self._eof()
            or self._check_kw("from")
            or self._check_kw("where")
            or self._check_kw("by")
            or (self.depth == 0 and self._check("NEWLINE"))
            or self._check("SEMI")
            or self._check("RPAREN")
            or self._check("RBRACKET")
            or self._check("RBRACE")
        )

    def _column(self) -> tuple[str | None, Node]:
        if self._check("IDENT") and self._peek_kind(1) == "COLON":
            name = self._advance().text
            self._advance()
            return name, self._expr()
        return None, self._expr()

    def _expr(self) -> Node:
        if self._check("DOLLAR") and self._peek_kind(1) == "LBRACKET":
            return self._cond()
        if self._at_verb():
            verb = self._verb()
            if self._can_start_expr():
                arg = self._expr()
                return Unary(verb.line, verb.col, verb.op, verb.adverb, arg)
            return verb
        left = self._noun()
        if self._at_infix():
            verb = self._verb()
            if verb.op == "dot":
                self.diagnostics.append(
                    unsupported(
                        "parse",
                        f"verb {verb.op} is outside the supported subset",
                        verb.line,
                        verb.col,
                    )
                )
                return UnsupportedNode(verb.line, verb.col, verb.op)
            right = self._expr()
            return Binary(verb.line, verb.col, verb.op, verb.adverb, left, right)
        return left

    def _noun(self) -> Node:
        items = [self._primary()]
        while self._at_primary():
            items.append(self._primary())
        if len(items) == 1:
            return items[0]
        if all(_data_literal(item) for item in items):
            return Strand(items[0].line, items[0].col, items)
        # Right-to-left application. A trailing run of data literals is one vector.
        split = len(items)
        while split > 1 and _data_literal(items[split - 1]):
            split -= 1
        # If everything after the first is data, split stays at 1.
        if split == len(items):
            # No trailing data vector; apply right-to-left across nouns.
            acc = items[-1]
            for fn in reversed(items[:-1]):
                acc = Apply(fn.line, fn.col, fn, [acc])
            return acc
        tail: Node
        tail_items = items[split:]
        tail = tail_items[0] if len(tail_items) == 1 else Strand(tail_items[0].line, tail_items[0].col, tail_items)
        acc = tail
        for fn in reversed(items[:split]):
            acc = Apply(fn.line, fn.col, fn, [acc])
        return acc

    def _primary(self) -> Node:
        node = self._atom()
        while self._match("LBRACKET"):
            self.depth += 1
            args = self._arg_list()
            self.depth -= 1
            self._expect("RBRACKET")
            node = Apply(node.line, node.col, node, args)
        if self._check("OVER") or self._check("SCAN") or self._check("EACH") or self._check("EACH_LEFT") or self._check("EACH_RIGHT") or self._check("EACH_PRIOR"):
            tok = self._peek()
            adverb = self._adverb()
            if isinstance(node, Verb):
                node.adverb = adverb
                return node
            if isinstance(node, Lambda) and adverb:
                return Derived(node.line, node.col, node, adverb)
            self.diagnostics.append(
                unsupported(
                    "parse",
                    "postfix iterator on this value is outside the supported subset; parenthesize primitive verbs such as (+/) or a lambda such as ({x+y}/)",
                    tok.line,
                    tok.col,
                )
            )
            return UnsupportedNode(tok.line, tok.col, "postfix iterator")
        return node

    def _atom(self) -> Node:
        tok = self._peek()
        if tok.kind == "NUMBER":
            self._advance()
            return Lit(tok.line, tok.col, tok.lit_type or "long", tok.lit_value, tok.null)
        if tok.kind == "BOOLS":
            self._advance()
            flags = tok.lit_value if isinstance(tok.lit_value, list) else []
            return Strand(
                tok.line,
                tok.col,
                [Lit(tok.line, tok.col, "bool", bool(item), False) for item in flags],
            )
        if tok.kind == "BYTES":
            self._advance()
            values = tok.lit_value if isinstance(tok.lit_value, list) else []
            return Strand(
                tok.line,
                tok.col,
                [Lit(tok.line, tok.col, "byte", item, False) for item in values],
            )
        if tok.kind in {"CHAR", "STRING", "SYMBOL"}:
            self._advance()
            if tok.kind == "STRING":
                text = tok.lit_value if isinstance(tok.lit_value, str) else ""
                return Strand(
                    tok.line,
                    tok.col,
                    [Lit(tok.line, tok.col, "char", None if ch == " " else ch, ch == " ") for ch in text],
                ) if text else ListLit(tok.line, tok.col, [], "char")
            return Lit(tok.line, tok.col, tok.lit_type or "symbol", tok.lit_value, tok.null)
        if tok.kind == "IDENT":
            self._advance()
            return Name(tok.line, tok.col, tok.text)
        if tok.kind == "LPAREN":
            return self._paren()
        if tok.kind == "LBRACE":
            return self._lambda()
        if tok.kind == "DOLLAR" and self._peek_kind(1) == "LBRACKET":
            return self._cond()
        self._advance()
        self.diagnostics.append(unsupported("parse", f"cannot parse {tok.text!r}", tok.line, tok.col))
        return UnsupportedNode(tok.line, tok.col, tok.text)

    def _cond(self) -> Node:
        tok = self._advance()
        self._expect("LBRACKET")
        self.depth += 1
        args = self._arg_list()
        self.depth -= 1
        self._expect("RBRACKET")
        if len(args) < 3 or len(args) % 2 == 0:
            self.diagnostics.append(
                unsupported("parse", "conditional $[...] needs an odd number of arguments >= 3", tok.line, tok.col)
            )
            return UnsupportedNode(tok.line, tok.col, "cond")
        return Cond(tok.line, tok.col, args)

    def _paren(self) -> Node:
        tok = self._advance()
        self.depth += 1
        if self._match("LBRACKET"):
            node = self._table(tok)
            self.depth -= 1
            return node
        if self._at_verb() and self._verb_group():
            verb = self._verb()
            self._expect("RPAREN")
            self.depth -= 1
            return verb
        if self._match("RPAREN"):
            self.depth -= 1
            return ListLit(tok.line, tok.col, [])
        items: list[Node] = [self._expr_or_empty()]
        semis = False
        while self._match("SEMI"):
            semis = True
            if self._check("RPAREN"):
                items.append(Empty(tok.line, tok.col))
                break
            items.append(self._expr_or_empty())
        self._expect("RPAREN")
        self.depth -= 1
        if not semis and len(items) == 1 and not isinstance(items[0], Empty):
            return items[0]
        return ListLit(tok.line, tok.col, items)

    def _table(self, tok: Token) -> Node:
        keys: list[tuple[str, Node]] = []
        if not self._check("RBRACKET"):
            keys = self._table_cols()
        self._expect("RBRACKET")
        cols: list[tuple[str, Node]] = []
        if not self._check("RPAREN"):
            cols = self._table_cols()
        self._expect("RPAREN")
        return TableLit(tok.line, tok.col, keys, cols)

    def _table_cols(self) -> list[tuple[str, Node]]:
        cols: list[tuple[str, Node]] = []
        if self._check("RBRACKET") or self._check("RPAREN"):
            return cols
        while not self._eof() and not self._check("RBRACKET") and not self._check("RPAREN"):
            if not self._check("IDENT"):
                self.diagnostics.append(error("parse", "expected column name", self._peek().line, self._peek().col))
                break
            name = self._advance().text
            self._expect("COLON")
            expr = self._expr()
            cols.append((name, expr))
            if not self._match("SEMI"):
                break
        return cols

    def _lambda(self) -> Node:
        tok = self._advance()
        self.depth += 1
        params: list[str] | None = None
        explicit = False
        if self._match("LBRACKET"):
            explicit = True
            params = []
            if not self._check("RBRACKET"):
                if self._check("IDENT"):
                    params.append(self._advance().text)
                    while self._match("SEMI"):
                        if self._check("IDENT"):
                            params.append(self._advance().text)
                else:
                    self.diagnostics.append(error("parse", "expected parameter", tok.line, tok.col))
            self._expect("RBRACKET")
        body: list[Node] = []
        self._skip_nl()
        while not self._eof() and not self._check("RBRACE"):
            body.append(self._stmt())
            if not self._skip_sep() and not self._check("RBRACE"):
                break
        self._expect("RBRACE")
        self.depth -= 1
        if params is None:
            params = _implicit_params(body)
        return Lambda(tok.line, tok.col, params, body, explicit)

    def _expr_or_empty(self) -> Node:
        if self._check("SEMI") or self._check("RPAREN") or self._check("RBRACKET"):
            tok = self._peek()
            return Empty(tok.line, tok.col)
        return self._expr()

    def _arg_list(self) -> list[Node]:
        args: list[Node] = []
        if self._check("RBRACKET"):
            return args
        args.append(self._expr_or_empty())
        while self._match("SEMI"):
            if self._check("RBRACKET"):
                args.append(Empty(self._peek().line, self._peek().col))
                break
            args.append(self._expr_or_empty())
        return args

    def _verb_group(self) -> bool:
        # Look ahead: verb, optional adverb keywords/glyphs, then RPAREN.
        j = self.i
        if j >= len(self.tokens):
            return False
        j += 1
        while j < len(self.tokens) and self.tokens[j].kind in {
            "EACH",
            "EACH_LEFT",
            "EACH_RIGHT",
            "EACH_PRIOR",
            "OVER",
            "SCAN",
        }:
            j += 1
        if j < len(self.tokens) and self.tokens[j].kind in {"EACH", "OVER", "SCAN", "PRIOR"}:
            j += 1
        return j < len(self.tokens) and self.tokens[j].kind == "RPAREN"

    def _verb(self) -> Verb:
        tok = self._advance()
        op = _op_of(tok)
        adverb = self._adverb()
        if tok.kind in {"OR", "AND", "DOT", "DOLLAR"}:
            op = {"OR": "or", "AND": "and", "DOT": "dot", "DOLLAR": "cast"}[tok.kind]
        return Verb(tok.line, tok.col, op, adverb)

    def _adverb(self) -> str | None:
        if self._check("EACH") or self._check_kw("each"):
            self._advance()
            return "each"
        if self._check("EACH_LEFT"):
            self._advance()
            return "each-left"
        if self._check("EACH_RIGHT"):
            self._advance()
            return "each-right"
        if self._check("EACH_PRIOR") or self._check_kw("prior"):
            self._advance()
            return "each-prior"
        if self._check("OVER") or self._check_kw("over"):
            self._advance()
            return "over"
        if self._check("SCAN") or self._check_kw("scan"):
            self._advance()
            return "scan"
        return None

    def _at_verb(self) -> bool:
        tok = self._peek()
        if tok.kind in _OP_KIND or tok.kind == "MINUS":
            return True
        if tok.text in _PREFIX:
            return True
        if tok.kind in {"OVER", "SCAN"}:
            return False
        if tok.text in _INFIX_WORDS and tok.kind == tok.text.upper():
            return False
        return False

    def _at_infix(self) -> bool:
        tok = self._peek()
        if self.depth == 0 and tok.kind == "NEWLINE":
            return False
        if tok.kind in _OP_KIND:
            return True
        return tok.text in _INFIX_WORDS

    def _at_primary(self) -> bool:
        if self._eof():
            return False
        if self.depth == 0 and self._check("NEWLINE"):
            return False
        if self._at_infix() or self._at_verb():
            return False
        tok = self._peek()
        return tok.kind in {"NUMBER", "BYTES", "CHAR", "STRING", "SYMBOL", "IDENT", "LPAREN", "LBRACE"}

    def _can_start_expr(self) -> bool:
        if self._eof():
            return False
        if self.depth == 0 and self._check("NEWLINE"):
            return False
        if self._check("SEMI") or self._check("RPAREN") or self._check("RBRACKET") or self._check("RBRACE"):
            return False
        if self._check("COMMA"):
            return False
        if self._check_kw("from") or self._check_kw("where") or self._check_kw("by"):
            return False
        return True

    def _skip_sep(self) -> bool:
        found = False
        while self._match("SEMI") or (self.depth == 0 and self._match("NEWLINE")) or (self.depth > 0 and self._match("NEWLINE")):
            found = True
        return found

    def _skip_nl(self) -> None:
        while self._match("NEWLINE"):
            pass

    def _match_kw(self, word: str) -> bool:
        if self._check_kw(word):
            self._advance()
            return True
        return False

    def _check_kw(self, word: str) -> bool:
        if self._eof():
            return False
        tok = self._peek()
        return tok.text == word and tok.kind == word.upper()

    def _match(self, kind: str) -> bool:
        if self._check(kind):
            self._advance()
            return True
        return False

    def _check(self, kind: str) -> bool:
        return not self._eof() and self._peek().kind == kind

    def _expect(self, kind: str) -> Token:
        if self._check(kind):
            return self._advance()
        tok = self._peek()
        self.diagnostics.append(error("parse", f"expected {kind} before {tok.text!r}", tok.line, tok.col))
        return tok

    def _advance(self) -> Token:
        tok = self._peek()
        if not self._eof():
            self.i += 1
        return tok

    def _peek(self) -> Token:
        if self.i >= len(self.tokens):
            return Token("EOF", "", 1, 1)
        return self.tokens[self.i]

    def _peek_kind(self, offset: int) -> str:
        index = self.i + offset
        if index >= len(self.tokens):
            return "EOF"
        return self.tokens[index].kind

    def _prev(self) -> Token:
        return self.tokens[self.i - 1]

    def _eof(self) -> bool:
        return self.i >= len(self.tokens)


def _implicit_params(body: list[Node]) -> list[str]:
    names = _names(body)
    if "z" in names:
        return ["x", "y", "z"]
    if "y" in names:
        return ["x", "y"]
    if "x" in names:
        return ["x"]
    return []


def _names(nodes: list[Node]) -> set[str]:
    found: set[str] = set()
    for node in nodes:
        if isinstance(node, Name):
            found.add(node.name)
        elif isinstance(node, Lambda):
            continue
        else:
            found |= _names(_child_nodes(node))
    return found


def _child_nodes(node: Node) -> list[Node]:
    if isinstance(node, Derived):
        return [node.fn]
    if isinstance(node, Unary):
        return [node.arg]
    if isinstance(node, Binary):
        return [node.left, node.right]
    if isinstance(node, Apply):
        return [node.fn, *node.args]
    if isinstance(node, (Strand, ListLit)):
        return list(node.items)
    if isinstance(node, Cond):
        return list(node.args)
    if isinstance(node, Assign):
        return [node.expr]
    if isinstance(node, Return):
        return [node.expr]
    if isinstance(node, Query):
        exprs = [expr for _, expr in node.cols]
        exprs += [expr for _, expr in node.by]
        if node.table is not None:
            exprs.append(node.table)
        if node.where is not None:
            exprs.append(node.where)
        return exprs
    if isinstance(node, TableLit):
        return [expr for _, expr in node.keys] + [expr for _, expr in node.cols]
    return []


def _data_literal(node: Node) -> bool:
    return isinstance(node, (Lit, Strand, ListLit))


def _op_of(tok: Token) -> str:
    if tok.kind in _OP_KIND:
        return _OP_KIND[tok.kind]
    if tok.kind == "MINUS":
        return "sub"
    if tok.text in _PREFIX or tok.text in _INFIX_WORDS:
        return tok.text if tok.text not in {"div", "mod"} else {"div": "div-int", "mod": "mod"}[tok.text]
    return tok.text
