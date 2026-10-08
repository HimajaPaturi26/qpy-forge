"""Q value model and canonical JSON.

Atoms, lists, dictionaries, and functions use plain Python. Tables also keep a
Polars frame for columnar filter and projection. See docs/type-mapping.md.
"""

from __future__ import annotations

import datetime as dt
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, cast

import polars as pl


class QError(Exception):
    def __init__(self, signal: str, message: str) -> None:
        self.signal = signal
        super().__init__(message)


@dataclass(frozen=True)
class Atom:
    typ: str
    null: bool = False
    value: object = None

    def __hash__(self) -> int:
        return hash((self.typ, self.null, _hashable(self.value)))


def _hashable(value: object) -> object:
    if isinstance(value, float) and math.isnan(value):
        return ("nan",)
    return value


@dataclass(frozen=True)
class Vec:
    etype: str
    items: tuple[Value, ...]


@dataclass(frozen=True)
class DictV:
    keys: tuple[Value, ...]
    vals: tuple[Value, ...]


@dataclass(frozen=True)
class TableV:
    columns: tuple[str, ...]
    types: tuple[tuple[str, str], ...]
    cols: tuple[tuple[Atom, ...], ...]
    keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class LambdaV:
    params: tuple[str, ...]
    arity: int
    call: Callable[[Env, tuple[Value, ...]], Value]
    label: str = "lambda"
    variadic: bool = False


@dataclass(frozen=True)
class ProjV:
    fn: LambdaV
    bound: tuple[Value | None, ...]


Value = Atom | Vec | DictV | TableV | LambdaV | ProjV


class Env:
    """q-like environment: locals, then the global root. No nested closures."""

    def __init__(self, parent: Env | None = None) -> None:
        self.locals: dict[str, Value] = {}
        self.parent = parent

    def root(self) -> Env:
        env: Env = self
        while env.parent is not None:
            env = env.parent
        return env

    def child_global(self) -> Env:
        return Env(parent=self.root())

    def set(self, name: str, value: Value) -> None:
        self.locals[name] = value

    def set_global(self, name: str, value: Value) -> None:
        self.root().locals[name] = value

    def get(self, name: str) -> Value:
        if name in self.locals:
            return self.locals[name]
        root = self.root()
        if root is not self and name in root.locals:
            return root.locals[name]
        raise QError("name", name)


class Scope:
    """Column scope used by qSQL. Column names shadow globals. `i` is the row index."""

    def __init__(self, columns: dict[str, list[Atom]], env: Env | None = None) -> None:
        self.columns = columns
        self.env = env

    def get(self, name: str) -> Value:
        if name in self.columns:
            return vec_of(self.columns[name])
        if self.env is not None:
            return self.env.get(name)
        raise QError("name", name)


TYPE_CODE: dict[str, int] = {
    "bool": 1,
    "byte": 4,
    "short": 5,
    "int": 6,
    "long": 7,
    "real": 8,
    "float": 9,
    "char": 10,
    "symbol": 11,
    "timestamp": 12,
    "month": 13,
    "date": 14,
    "timespan": 16,
    "minute": 17,
    "second": 18,
    "time": 19,
}

_INT_BITS: dict[str, int] = {"byte": 8, "short": 16, "int": 32, "long": 64}
_INT_RANK: dict[str, int] = {"bool": 0, "byte": 1, "short": 2, "int": 3, "long": 4}
_POLARS: dict[str, pl.DataType] = {
    "bool": pl.Boolean(),
    "byte": pl.UInt8(),
    "short": pl.Int16(),
    "int": pl.Int32(),
    "long": pl.Int64(),
    "real": pl.Float32(),
    "float": pl.Float64(),
    "char": pl.Utf8(),
    "symbol": pl.Utf8(),
    "date": pl.Date(),
    "timestamp": pl.Datetime(time_unit="ns"),
    "month": pl.Utf8(),
}


def wrap_int(typ: str, number: int) -> int:
    bits = _INT_BITS[typ]
    masked = number & ((1 << bits) - 1)
    if typ != "byte" and masked >= (1 << (bits - 1)):
        masked -= 1 << bits
    return masked


def long(number: int) -> Atom:
    return Atom("long", value=wrap_int("long", number))


def short(number: int) -> Atom:
    return Atom("short", value=wrap_int("short", number))


def int_(number: int) -> Atom:
    return Atom("int", value=wrap_int("int", number))


def byte(number: int) -> Atom:
    return Atom("byte", value=wrap_int("byte", number))


def float_(number: float) -> Atom:
    if math.isnan(number):
        return Atom("float", null=True)
    return Atom("float", value=float(number))


def boolean(flag: bool) -> Atom:
    return Atom("bool", value=bool(flag))


def char(text: str, *, null: bool = False) -> Atom:
    if null or text == " ":
        return Atom("char", null=True)
    return Atom("char", value=text)


def symbol(text: str) -> Atom:
    return Atom("symbol", value=text)


def date(year: int, month: int, day: int) -> Atom:
    return Atom("date", value=dt.date(year, month, day))


def null(typ: str) -> Atom:
    return Atom(typ, null=True)


def vec_of(items: Sequence[Value]) -> Vec:
    if not items:
        return Vec("general", ())
    types = [_etype_of(item) for item in items]
    if all(item == types[0] and not isinstance(items[0], (Vec, DictV, TableV, LambdaV, ProjV)) for item in types):
        et = types[0]
        if et is not None and all(isinstance(item, Atom) for item in items):
            return Vec(et, tuple(items))
    return Vec("general", tuple(items))


def _etype_of(item: Value) -> str | None:
    if isinstance(item, Atom):
        return item.typ
    return None


def is_atom(value: Value) -> bool:
    return isinstance(value, Atom)


def as_atoms(value: Value) -> list[Atom] | None:
    if isinstance(value, Atom):
        return [value]
    if isinstance(value, Vec) and all(isinstance(item, Atom) for item in value.items):
        return [cast(Atom, item) for item in value.items]
    return None


def canon(value: Value) -> dict[str, Any]:
    if isinstance(value, Atom):
        if value.null:
            return {"t": value.typ, "null": True}
        return {"t": value.typ, "v": _encode_atom(value)}
    if isinstance(value, Vec):
        return {"t": "list", "etype": value.etype, "v": [canon(item) for item in value.items]}
    if isinstance(value, DictV):
        return {
            "t": "dict",
            "keys": [canon(item) for item in value.keys],
            "vals": [canon(item) for item in value.vals],
        }
    if isinstance(value, TableV):
        rows: list[dict[str, Any]] = []
        count = len(value.cols[0]) if value.cols else 0
        for index in range(count):
            row: dict[str, Any] = {}
            for name, column in zip(value.columns, value.cols, strict=True):
                row[name] = canon(column[index])
            rows.append(row)
        return {
            "t": "keyed" if value.keys else "table",
            "keys": list(value.keys),
            "cols": list(value.columns),
            "types": {name: typ for name, typ in value.types},
            "rows": rows,
        }
    if isinstance(value, LambdaV):
        return {"t": "lambda", "params": list(value.params), "label": value.label}
    if isinstance(value, ProjV):
        return {
            "t": "projection",
            "params": list(value.fn.params),
            "bound": [None if item is None else canon(item) for item in value.bound],
        }
    raise TypeError(f"cannot canonize {type(value)!r}")


def _encode_atom(atom: Atom) -> object:
    if isinstance(atom.value, float):
        if math.isinf(atom.value):
            return "inf" if atom.value > 0 else "-inf"
        return atom.value
    if isinstance(atom.value, dt.datetime):
        return atom.value.isoformat()
    if isinstance(atom.value, dt.date):
        return atom.value.isoformat()
    if isinstance(atom.value, bool):
        return bool(atom.value)
    return atom.value


def q_repr(value: Value) -> str:
    if isinstance(value, Atom):
        return _repr_atom(value)
    if isinstance(value, Vec):
        if value.etype == "char":
            chars = []
            for item in value.items:
                assert isinstance(item, Atom)
                chars.append(" " if item.null else str(item.value))
            return '"' + "".join(chars) + '"'
        if value.etype == "bool" and all(isinstance(item, Atom) for item in value.items):
            bits = []
            for item in value.items:
                assert isinstance(item, Atom)
                bits.append("0" if item.null or not item.value else "1")
            return "".join(bits) + "b"
        if value.etype == "symbol":
            parts = []
            for item in value.items:
                assert isinstance(item, Atom)
                parts.append("`" + ("" if item.null else str(item.value)))
            return "".join(parts)
        inner = " ".join(q_repr(item) for item in value.items)
        if value.etype == "general":
            return "(" + ";".join(q_repr(item) for item in value.items) + ")"
        return inner
    if isinstance(value, DictV):
        return q_repr(Vec("general", value.keys)) + "!" + q_repr(Vec("general", value.vals))
    if isinstance(value, TableV):
        header = " ".join(value.columns)
        lines = [header]
        count = len(value.cols[0]) if value.cols else 0
        for index in range(count):
            lines.append(" ".join(q_repr(column[index]) for column in value.cols))
        if value.keys:
            return "keyed[" + ",".join(value.keys) + "]\n" + "\n".join(lines)
        return "\n".join(lines)
    if isinstance(value, LambdaV):
        return "{" + ";".join(value.params) + "}"
    if isinstance(value, ProjV):
        shown = ["" if item is None else q_repr(item) for item in value.bound]
        return q_repr(value.fn) + "[" + ";".join(shown) + "]"
    return str(value)


def _repr_atom(atom: Atom) -> str:
    if atom.null:
        return {
            "long": "0N",
            "int": "0Ni",
            "short": "0Nh",
            "float": "0n",
            "real": "0Ne",
            "bool": "0b",
            "char": '" "',
            "symbol": "`",
            "date": "0Nd",
            "timestamp": "0Np",
        }.get(atom.typ, "0N")
    if atom.typ == "bool":
        return "1b" if atom.value else "0b"
    if atom.typ == "char":
        return '"' + str(atom.value) + '"'
    if atom.typ == "symbol":
        return "`" + str(atom.value)
    if atom.typ == "float":
        assert isinstance(atom.value, float)
        if math.isinf(atom.value):
            return "0w" if atom.value > 0 else "-0w"
        text = repr(atom.value)
        return text if "." in text or "e" in text else text + ".0"
    if atom.typ == "short":
        return str(atom.value) + "h"
    if atom.typ == "int":
        return str(atom.value) + "i"
    if atom.typ == "byte":
        return str(atom.value) + "x"
    return str(atom.value)


def to_frame(table: TableV) -> pl.DataFrame:
    """Columnar copy used by select/update/delete filters."""
    series: list[pl.Series] = []
    types = dict(table.types)
    for name, column in zip(table.columns, table.cols, strict=True):
        typ = types[name]
        dtype = _POLARS.get(typ, pl.Object())
        data = [_frame_cell(atom, typ) for atom in column]
        series.append(pl.Series(name, data, dtype=dtype))
    if not series:
        return pl.DataFrame()
    return pl.DataFrame(series)


def filter_table(table: TableV, mask: list[bool]) -> TableV:
    if len(mask) != (len(table.cols[0]) if table.cols else 0):
        raise QError("length", "where mask length")
    frame = to_frame(table)
    if frame.width == 0:
        return table
    filtered = frame.filter(pl.Series("__mask", mask))
    return _table_from_frame(filtered, table)


def _frame_cell(atom: Atom, typ: str) -> object:
    if atom.null:
        return None
    if typ == "char":
        return str(atom.value)
    if typ == "month":
        assert isinstance(atom.value, tuple)
        year, month = atom.value
        return f"{year:04d}-{month:02d}"
    return atom.value


def _table_from_frame(frame: pl.DataFrame, original: TableV) -> TableV:
    types = dict(original.types)
    columns: list[str] = []
    cols: list[tuple[Atom, ...]] = []
    type_pairs: list[tuple[str, str]] = []
    for name in original.columns:
        if name not in frame.columns:
            continue
        typ = types[name]
        atoms = tuple(_atom_from_cell(cell, typ) for cell in frame.get_column(name).to_list())
        columns.append(name)
        cols.append(atoms)
        type_pairs.append((name, typ))
    keys = tuple(key for key in original.keys if key in columns)
    return TableV(tuple(columns), tuple(type_pairs), tuple(cols), keys)


def _atom_from_cell(cell: object, typ: str) -> Atom:
    if cell is None:
        return Atom(typ, null=True)
    if typ == "char":
        return char(str(cell))
    if typ == "bool":
        return boolean(bool(cell))
    if typ == "float":
        return float_(float(cast(float, cell)))
    if typ == "symbol":
        return symbol(str(cell))
    if typ == "date":
        if isinstance(cell, dt.datetime):
            return Atom("date", value=cell.date())
        if isinstance(cell, dt.date):
            return Atom("date", value=cell)
    if typ in _INT_BITS or typ == "long":
        return Atom(typ, value=int(cast(int, cell)))
    if typ == "month" and isinstance(cell, str):
        year, month = cell.split("-")
        return Atom("month", value=(int(year), int(month)))
    return Atom(typ, value=cell)


def table_from_columns(
    names: list[str],
    columns: list[list[Atom]],
    keys: list[str] | None = None,
) -> TableV:
    if len(names) != len(columns):
        raise QError("length", "column names")
    if not names:
        return TableV((), (), (), tuple(keys or ()))
    width = len(columns[0])
    if any(len(column) != width for column in columns):
        raise QError("length", "column length")
    types = tuple((name, column[0].typ if column else "general") for name, column in zip(names, columns, strict=True))
    # Empty columns keep a declared type of long only when we have no atom. Callers pass typed empties
    # via Atom lists. An empty column has no atom to read; default long is wrong for symbols.
    # Preserve caller type by inspecting a sentinel: empty list uses "general" unless names carry types
    # through non-empty siblings. Callers that need a typed empty pass one null of that type and then
    # drop it — the select path always has atoms or an explicit type. Handled in build_table.
    return TableV(tuple(names), types, tuple(tuple(column) for column in columns), tuple(keys or ()))
