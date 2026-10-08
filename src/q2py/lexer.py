"""Lexer for the supported q subset.

Comment and minus-sign rules follow the public q syntax guide: a slash preceded
by a blank or newline starts a comment, and a minus sign is a negative literal
unless it is glued to a name, constant, right parenthesis, or right bracket.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from q2py.diagnostics import Diagnostic, unsupported


@dataclass
class Token:
    kind: str
    text: str
    line: int
    col: int
    lit_type: str | None = None
    lit_value: object = None
    null: bool = False


@dataclass
class LexResult:
    tokens: list[Token]
    diagnostics: list[Diagnostic] = field(default_factory=list)


_INFIX_GLYPHS = set("+-*%=<>~,#_!$?@.|&^")
_TWO = ("<=", ">=", "<>", "/:", "\\:", "':", "::")
_KEYWORDS = {
    "select",
    "exec",
    "update",
    "delete",
    "from",
    "where",
    "by",
    "each",
    "over",
    "scan",
    "prior",
    "div",
    "mod",
    "in",
    "xbar",
    "rotate",
    "except",
    "inter",
    "union",
}


def lex(source: str) -> LexResult:
    lexer = _Lexer(source)
    return lexer.run()


class _Lexer:
    def __init__(self, source: str) -> None:
        self.source = source.replace("\r\n", "\n").replace("\r", "\n")
        self.n = len(self.source)
        self.i = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []
        self.diagnostics: list[Diagnostic] = []
        self.line_start = True

    def run(self) -> LexResult:
        while self.i < self.n:
            if self._block_or_exit():
                break
            self._skip_spaces()
            if self.i >= self.n:
                break
            if self.source[self.i] == "\n":
                self._newline()
                continue
            if self._comment():
                continue
            start_line, start_col = self.line, self.col
            token = self._token()
            if token is None:
                ch = self.source[self.i]
                self.diagnostics.append(
                    unsupported("lex", f"unsupported character {ch!r}", start_line, start_col, "Q2PY100")
                )
                self._bump()
                continue
            self.tokens.append(token)
            self.line_start = False
        return LexResult(self.tokens, self.diagnostics)

    def _block_or_exit(self) -> bool:
        if not self.line_start:
            return False
        if self._line_is("/"):
            # Multiline comment until a singleton backslash line.
            self._consume_line()
            while self.i < self.n and not self._line_is("\\"):
                self._consume_line()
            if self.i < self.n:
                self._consume_line()
            return False
        if self._line_is("\\"):
            # Singleton backslash ends the script.
            return True
        return False

    def _line_is(self, glyph: str) -> bool:
        j = self.i
        while j < self.n and self.source[j] in " \t":
            j += 1
        if j >= self.n or self.source[j] != glyph:
            return False
        k = j + 1
        while k < self.n and self.source[k] in " \t":
            k += 1
        return k >= self.n or self.source[k] == "\n"

    def _consume_line(self) -> None:
        while self.i < self.n and self.source[self.i] != "\n":
            self._bump()
        if self.i < self.n and self.source[self.i] == "\n":
            self._bump()
        self.line_start = True

    def _comment(self) -> bool:
        ch = self.source[self.i]
        if ch != "/":
            return False
        prev_blank = self.i == 0 or self.source[self.i - 1] in " \t\n"
        if self.line_start or prev_blank:
            # Glued `/:` is an adverb only when not preceded by a blank.
            self.tokens.append(Token("COMMENT", self._rest_of_line(), self.line, self.col))
            while self.i < self.n and self.source[self.i] != "\n":
                self._bump()
            return True
        return False

    def _rest_of_line(self) -> str:
        j = self.i
        while j < self.n and self.source[j] != "\n":
            j += 1
        return self.source[self.i : j]

    def _skip_spaces(self) -> None:
        while self.i < self.n and self.source[self.i] in " \t":
            self._bump()

    def _newline(self) -> None:
        self.tokens.append(Token("NEWLINE", "\n", self.line, self.col))
        self._bump()
        self.line_start = True

    def _token(self) -> Token | None:
        line, col = self.line, self.col
        ch = self.source[self.i]
        if ch == '"':
            return self._string(line, col)
        if ch == "`":
            return self._symbol(line, col)
        if ch == "-" and self._negative_literal():
            return self._number(line, col, negative=True)
        if ch.isdigit():
            return self._number(line, col, negative=False)
        two = self.source[self.i : self.i + 2]
        if two in _TWO:
            self._bump()
            self._bump()
            kind = {
                "<=": "LE",
                ">=": "GE",
                "<>": "NE",
                "/:": "EACH_RIGHT",
                "\\:": "EACH_LEFT",
                "':": "EACH_PRIOR",
                "::": "ASSIGN_GLOBAL",
            }[two]
            return Token(kind, two, line, col)
        if ch == "/" and (self.i == 0 or self.source[self.i - 1] not in " \t\n"):
            self._bump()
            return Token("OVER", "/", line, col)
        if ch == "\\" and (self.i == 0 or self.source[self.i - 1] not in " \t\n"):
            self._bump()
            return Token("SCAN", "\\", line, col)
        if ch == "\\":
            self.diagnostics.append(
                unsupported("lex", "backslash is outside the supported subset", line, col, "Q2PY104")
            )
            self._bump()
            return Token("UNSUPPORTED", "\\", line, col)
        if ch == ":":
            self._bump()
            return Token("COLON", ":", line, col)
        if ch in _INFIX_GLYPHS or ch in "()[]{};":
            self._bump()
            return Token(_kind(ch), ch, line, col)
        if ch == "'" and (self.i == 0 or self.source[self.i - 1] not in " \t\n"):
            self._bump()
            return Token("EACH", "'", line, col)
        if ch == "." and self.i + 1 < self.n and (self.source[self.i + 1].isalpha() or self.source[self.i + 1] == "."):
            return self._ident(line, col)
        if ch.isalpha() or ch == "_" or ch == ".":
            return self._ident(line, col)
        return None

    def _negative_literal(self) -> bool:
        if self.i + 1 >= self.n or not self.source[self.i + 1].isdigit():
            return False
        prev = self._prev_significant()
        glued = self.i > 0 and self.source[self.i - 1] not in " \t\n"
        if glued and prev in {"IDENT", "NUMBER", "STRING", "SYMBOL", "RPAREN", "RBRACKET"}:
            return False
        return True

    def _prev_significant(self) -> str | None:
        for token in reversed(self.tokens):
            if token.kind not in {"NEWLINE", "COMMENT"}:
                return token.kind
        return None

    def _string(self, line: int, col: int) -> Token:
        self._bump()
        chars: list[str] = []
        while self.i < self.n and self.source[self.i] != '"':
            if self.source[self.i] == "\\" and self.i + 1 < self.n:
                nxt = self.source[self.i + 1]
                mapping = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"'}
                chars.append(mapping.get(nxt, nxt))
                self._bump()
                self._bump()
                continue
            chars.append(self.source[self.i])
            self._bump()
        if self.i >= self.n:
            self.diagnostics.append(unsupported("lex", "unterminated string", line, col, "Q2PY101"))
        else:
            self._bump()
        if len(chars) == 1:
            atom = chars[0]
            if atom == " ":
                return Token("CHAR", '" "', line, col, "char", None, True)
            return Token("CHAR", '"' + atom + '"', line, col, "char", atom, False)
        return Token("STRING", '"' + "".join(chars) + '"', line, col, "char", "".join(chars), False)

    def _symbol(self, line: int, col: int) -> Token:
        self._bump()
        start = self.i
        while self.i < self.n and (self.source[self.i].isalnum() or self.source[self.i] in "._"):
            self._bump()
        text = self.source[start : self.i]
        return Token("SYMBOL", "`" + text, line, col, "symbol", text, text == "")

    def _ident(self, line: int, col: int) -> Token:
        start = self.i
        self._bump()
        while self.i < self.n and (self.source[self.i].isalnum() or self.source[self.i] in "._"):
            self._bump()
        text = self.source[start : self.i]
        if text in _KEYWORDS:
            return Token(text.upper(), text, line, col)
        return Token("IDENT", text, line, col)

    def _number(self, line: int, col: int, *, negative: bool) -> Token:
        if negative:
            self._bump()
        start = self.i
        special = self._special_atom(negative, line, col)
        if special is not None:
            return special
        if self.source.startswith("0x", self.i) or self.source.startswith("0X", self.i):
            return self._bytes(line, col, negative)
        temporal = self._temporal(negative, line, col)
        if temporal is not None:
            return temporal
        while self.i < self.n and self.source[self.i].isdigit():
            self._bump()
        is_float = False
        if self.i < self.n and self.source[self.i] == "." and self.i + 1 < self.n and self.source[self.i + 1].isdigit():
            is_float = True
            self._bump()
            while self.i < self.n and self.source[self.i].isdigit():
                self._bump()
        if self.i < self.n and self.source[self.i] in "eE":
            is_float = True
            self._bump()
            if self.i < self.n and self.source[self.i] in "+-":
                self._bump()
            while self.i < self.n and self.source[self.i].isdigit():
                self._bump()
        suffix = ""
        if self.i < self.n and self.source[self.i] in "hjfeb":
            # `b` is boolean only for 0 and 1. A trailing ident letter is not a suffix.
            nxt = self.i + 1
            boundary = nxt >= self.n or not (self.source[nxt].isalnum() or self.source[nxt] == "_")
            if boundary:
                suffix = self.source[self.i]
                self._bump()
        body = self.source[start : self.i]
        shown = ("-" if negative else "") + body
        if suffix == "b":
            bits = body[:-1]
            if bits and all(ch in "01" for ch in bits):
                if len(bits) == 1:
                    return Token("NUMBER", shown, line, col, "bool", bits == "1", False)
                if negative:
                    self.diagnostics.append(unsupported("lex", f"invalid boolean {shown}", line, col, "Q2PY102"))
                flags = [ch == "1" for ch in bits]
                return Token("BOOLS", shown, line, col, "bool", flags, False)
            self.diagnostics.append(unsupported("lex", f"invalid boolean {shown}", line, col, "Q2PY102"))
            return Token("NUMBER", shown, line, col, "bool", False, False)
        if is_float or suffix in {"f", "e"}:
            numeric = body[:-1] if suffix in {"f", "e"} else body
            number = float(numeric)
            if negative:
                number = -number
            typ = "real" if suffix == "e" else "float"
            return Token("NUMBER", shown, line, col, typ, number, False)
        digits = body[:-1] if suffix else body
        number_i = int(digits)
        if negative:
            number_i = -number_i
        typ = {"": "long", "j": "long", "h": "short", "i": "int"}.get(suffix, "long")
        return Token("NUMBER", shown, line, col, typ, number_i, False)

    def _special_atom(self, negative: bool, line: int, col: int) -> Token | None:
        rest = self.source[self.i :]
        sign = "-" if negative else ""
        options = [
            ("0Nw", "float", None, True),
            ("0W", "long", None, True),
            ("0w", "float", float("inf"), False),
            ("0n", "float", None, True),
            ("0N", "long", None, True),
        ]
        typed = {
            "h": "short",
            "i": "int",
            "j": "long",
            "e": "real",
            "f": "float",
            "b": "bool",
            "d": "date",
            "p": "timestamp",
            "m": "month",
            "t": "time",
            "v": "second",
            "u": "minute",
            "n": "timespan",
        }
        for lexeme, typ, value, is_null in options:
            if rest.startswith(lexeme) and self._boundary(self.i + len(lexeme)):
                if lexeme == "0N" and len(rest) > 2 and rest[2] in typed:
                    continue
                self.i += len(lexeme)
                self.col += len(lexeme)
                if lexeme == "0w" and negative:
                    value = float("-inf")
                if lexeme == "0W":
                    # 0W is q's integer infinity stand-in, the max signed long. Not a null.
                    is_null = False
                    value = -9223372036854775808 if negative else 9223372036854775807
                    typ = "long"
                return Token("NUMBER", sign + lexeme, line, col, typ, value, is_null)
        if rest.startswith("0N") and len(rest) > 2 and rest[2] in typed and self._boundary(self.i + 3):
            suffix = rest[2]
            self.i += 3
            self.col += 3
            return Token("NUMBER", sign + "0N" + suffix, line, col, typed[suffix], None, True)
        return None

    def _bytes(self, line: int, col: int, negative: bool) -> Token:
        self.i += 2
        self.col += 2
        start = self.i
        while self.i < self.n and self.source[self.i] in "0123456789abcdefABCDEF":
            self._bump()
        hex_text = self.source[start : self.i]
        if not hex_text or len(hex_text) % 2:
            self.diagnostics.append(unsupported("lex", "invalid byte literal", line, col, "Q2PY103"))
            return Token("NUMBER", "0x" + hex_text, line, col, "byte", 0, False)
        values = [int(hex_text[k : k + 2], 16) for k in range(0, len(hex_text), 2)]
        if len(values) == 1:
            return Token("NUMBER", "0x" + hex_text, line, col, "byte", values[0], False)
        return Token("BYTES", "0x" + hex_text, line, col, "byte", values, False)

    def _temporal(self, negative: bool, line: int, col: int) -> Token | None:
        import re

        rest = self.source[self.i :]
        timestamp = re.match(r"(\d{4})\.(\d{2})\.(\d{2})D(\d{2}):(\d{2}):(\d{2})(\.\d+)?", rest)
        if timestamp and self._boundary(self.i + timestamp.end()):
            self._advance(timestamp.end())
            import datetime as dt

            frac = timestamp.group(7) or ".0"
            micro = int(float(frac) * 1_000_000)
            value: object = dt.datetime(
                int(timestamp.group(1)),
                int(timestamp.group(2)),
                int(timestamp.group(3)),
                int(timestamp.group(4)),
                int(timestamp.group(5)),
                int(timestamp.group(6)),
                micro,
            )
            return Token("NUMBER", timestamp.group(0), line, col, "timestamp", value, False)
        date = re.match(r"(\d{4})\.(\d{2})\.(\d{2})", rest)
        if date and self._boundary(self.i + date.end()) and not (self.i + date.end() < self.n and self.source[self.i + date.end()] == "D"):
            self._advance(date.end())
            import datetime as dt

            value = dt.date(int(date.group(1)), int(date.group(2)), int(date.group(3)))
            return Token("NUMBER", date.group(0), line, col, "date", value, False)
        month = re.match(r"(\d{4})\.(\d{2})m", rest)
        if month and self._boundary(self.i + month.end()):
            self._advance(month.end())
            return Token("NUMBER", month.group(0), line, col, "month", (int(month.group(1)), int(month.group(2))), False)
        return None

    def _boundary(self, index: int) -> bool:
        if index >= self.n:
            return True
        return not (self.source[index].isalnum() or self.source[index] == "_")

    def _advance(self, count: int) -> None:
        for _ in range(count):
            self._bump()

    def _bump(self) -> None:
        if self.source[self.i] == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        self.i += 1


def _kind(ch: str) -> str:
    return {
        "+": "PLUS",
        "-": "MINUS",
        "*": "STAR",
        "%": "PERCENT",
        "=": "EQ",
        "<": "LT",
        ">": "GT",
        "~": "MATCH",
        ",": "COMMA",
        "#": "TAKE",
        "_": "DROP",
        "!": "BANG",
        "$": "DOLLAR",
        "?": "QUERY",
        "@": "AT",
        ".": "DOT",
        "|": "OR",
        "&": "AND",
        "^": "FILL",
        "(": "LPAREN",
        ")": "RPAREN",
        "[": "LBRACKET",
        "]": "RBRACKET",
        "{": "LBRACE",
        "}": "RBRACE",
        ";": "SEMI",
    }[ch]
