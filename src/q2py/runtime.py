"""Q semantics for the supported subset.

Generated Python calls this module. It does not parse q and it does not invent
results for constructs the semantic pass refused.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import cast

from q2py.values import (
    TYPE_CODE,
    Atom,
    DictV,
    Env,
    LambdaV,
    ProjV,
    Scope,
    TableV,
    Value,
    Vec,
    boolean,
    char,
    filter_table,
    float_,
    long,
    null,
    q_repr,
    short,
    symbol,
    table_from_columns,
    vec_of,
    wrap_int,
)
from q2py.values import QError as QError
from q2py.values import byte as byte
from q2py.values import date as date
from q2py.values import int_ as int_

_NUMERIC = {"bool", "byte", "short", "int", "long", "real", "float"}
_INTS = {"bool", "byte", "short", "int", "long"}


def _atoms(value: Value) -> list[Atom]:
    if isinstance(value, Atom):
        return [value]
    if isinstance(value, Vec):
        out: list[Atom] = []
        for item in value.items:
            if not isinstance(item, Atom):
                raise QError("type", "expected atoms")
            out.append(item)
        return out
    raise QError("type", "expected atom or list")


def _promote(left: str, right: str) -> str:
    if left == "date" or right == "date":
        return "date"
    if "float" in (left, right) or "real" in (left, right):
        return "float"
    if left == "bool" and right == "bool":
        return "int"
    rank = {"bool": 0, "byte": 1, "short": 2, "int": 3, "long": 4}
    return "long" if rank[left] >= 4 or rank[right] >= 4 else ("int" if max(rank[left], rank[right]) >= 3 else ("short" if max(rank[left], rank[right]) >= 2 else "byte"))


def _as_float(atom: Atom) -> float:
    if atom.null:
        return float("nan")
    if atom.typ == "bool":
        return 1.0 if atom.value else 0.0
    if isinstance(atom.value, bool):
        return 1.0 if atom.value else 0.0
    return float(cast(float | int, atom.value))


def _as_int(atom: Atom) -> int:
    if atom.null:
        raise QError("type", "null integer")
    if atom.typ == "bool":
        return 1 if atom.value else 0
    return int(cast(int, atom.value))


def _num(atom: Atom, typ: str) -> Atom:
    if typ == "float":
        return float_(_as_float(atom))
    if typ == "bool":
        return boolean(bool(_as_int(atom)))
    return Atom(typ, value=wrap_int(typ, _as_int(atom)))


def _finish(typ: str, raw: float | int, *, float_op: bool) -> Atom:
    if float_op or typ == "float":
        if isinstance(raw, float) and math.isnan(raw):
            return null("float")
        return float_(float(raw))
    return Atom(typ, value=wrap_int(typ, int(raw)))


def _apply_atom(op: str, left: Atom, right: Atom) -> Atom:
    if op in {"add", "sub"} and (left.typ == "date" or right.typ == "date"):
        return _date_arith(op, left, right)
    if left.typ not in _NUMERIC or right.typ not in _NUMERIC:
        raise QError("type", op)
    if left.null or right.null:
        return null(_promote(left.typ, right.typ) if op != "div" else "float")
    typ = "float" if op == "div" else _promote(left.typ, right.typ)
    lf = _as_float(left)
    rf = _as_float(right)
    if op == "add":
        raw: float | int = lf + rf
    elif op == "sub":
        raw = lf - rf
    elif op == "mul":
        raw = lf * rf
    elif op == "div":
        if rf == 0.0:
            if lf == 0.0:
                return null("float")
            return float_(math.inf if lf > 0 else -math.inf)
        raw = lf / rf
        return float_(float(raw))
    else:
        raise QError("nyi", op)
    if typ == "float":
        return float_(float(raw))
    return _finish(typ, int(raw) if typ != "float" else raw, float_op=False)


def _date_arith(op: str, left: Atom, right: Atom) -> Atom:
    import datetime as dt

    if left.null or right.null:
        if op == "sub" and left.typ == "date" and right.typ == "date":
            return null("long")
        return null("date")
    if op == "add":
        base, offset = (left, right) if left.typ == "date" else (right, left)
        if base.typ != "date" or offset.typ not in _INTS:
            raise QError("type", "date add")
        assert isinstance(base.value, dt.date)
        return Atom("date", value=base.value + dt.timedelta(days=_as_int(offset)))
    if left.typ == "date" and right.typ == "date":
        assert isinstance(left.value, dt.date) and isinstance(right.value, dt.date)
        return long((left.value - right.value).days)
    if left.typ == "date" and right.typ in _INTS:
        assert isinstance(left.value, dt.date)
        return Atom("date", value=left.value - dt.timedelta(days=_as_int(right)))
    raise QError("type", "date sub")


def atomic_bin(op: str, left: Value, right: Value) -> Value:
    if isinstance(left, Atom) and isinstance(right, Atom):
        return _apply_atom(op, left, right)
    if isinstance(left, Vec) and isinstance(right, Atom):
        return vec_of([atomic_bin(op, item, right) for item in left.items])
    if isinstance(left, Atom) and isinstance(right, Vec):
        return vec_of([atomic_bin(op, left, item) for item in right.items])
    if isinstance(left, Vec) and isinstance(right, Vec):
        if len(left.items) != len(right.items):
            raise QError("length", op)
        return vec_of([atomic_bin(op, a, b) for a, b in zip(left.items, right.items, strict=True)])
    if isinstance(left, DictV) and isinstance(right, Atom):
        return DictV(left.keys, tuple(cast(Vec, atomic_bin(op, Vec("general", left.vals), right)).items))
    if isinstance(left, Atom) and isinstance(right, DictV):
        return DictV(right.keys, tuple(cast(Vec, atomic_bin(op, left, Vec("general", right.vals))).items))
    raise QError("type", op)


def add(left: Value, right: Value) -> Value:
    return atomic_bin("add", left, right)


def sub(left: Value, right: Value) -> Value:
    return atomic_bin("sub", left, right)


def mul(left: Value, right: Value) -> Value:
    return atomic_bin("mul", left, right)


def div(left: Value, right: Value) -> Value:
    return atomic_bin("div", left, right)


def _cmp_atom(op: str, left: Atom, right: Atom) -> Atom:
    if left.null or right.null:
        return boolean(False)
    if type(left.value) is not type(right.value) and not (
        isinstance(left.value, (int, float, bool)) and isinstance(right.value, (int, float, bool))
    ):
        if op == "eq":
            return boolean(False)
        if op == "ne":
            return boolean(True)
        raise QError("type", op)
    lv: object = int(cast(int, left.value)) if left.typ == "bool" else left.value
    rv: object = int(cast(int, right.value)) if right.typ == "bool" else right.value
    if isinstance(lv, (int, float, bool)) and isinstance(rv, (int, float, bool)):
        lnum = float(lv)
        rnum = float(rv)
        result = {
            "eq": lnum == rnum,
            "ne": lnum != rnum,
            "lt": lnum < rnum,
            "gt": lnum > rnum,
            "le": lnum <= rnum,
            "ge": lnum >= rnum,
        }[op]
        return boolean(result)
    result = {
        "eq": lv == rv,
        "ne": lv != rv,
        "lt": lv < rv,  # type: ignore[operator]
        "gt": lv > rv,  # type: ignore[operator]
        "le": lv <= rv,  # type: ignore[operator]
        "ge": lv >= rv,  # type: ignore[operator]
    }[op]
    return boolean(bool(result))


def _cmp(op: str, left: Value, right: Value) -> Value:
    if isinstance(left, Atom) and isinstance(right, Atom):
        return _cmp_atom(op, left, right)
    if isinstance(left, Vec) and isinstance(right, Atom):
        return vec_of([_cmp(op, item, right) for item in left.items])
    if isinstance(left, Atom) and isinstance(right, Vec):
        return vec_of([_cmp(op, left, item) for item in right.items])
    if isinstance(left, Vec) and isinstance(right, Vec):
        if len(left.items) != len(right.items):
            raise QError("length", op)
        return vec_of([_cmp(op, a, b) for a, b in zip(left.items, right.items, strict=True)])
    raise QError("type", op)


def eq(left: Value, right: Value) -> Value:
    return _cmp("eq", left, right)


def ne(left: Value, right: Value) -> Value:
    return _cmp("ne", left, right)


def lt(left: Value, right: Value) -> Value:
    return _cmp("lt", left, right)


def gt(left: Value, right: Value) -> Value:
    return _cmp("gt", left, right)


def le(left: Value, right: Value) -> Value:
    return _cmp("le", left, right)


def ge(left: Value, right: Value) -> Value:
    return _cmp("ge", left, right)


def match(left: Value, right: Value) -> Atom:
    return boolean(_match(left, right))


def _match(left: Value, right: Value) -> bool:
    if isinstance(left, Atom) and isinstance(right, Atom):
        if left.typ != right.typ:
            return False
        if left.null or right.null:
            return left.null and right.null
        return left.value == right.value
    if isinstance(left, Vec) and isinstance(right, Vec):
        return len(left.items) == len(right.items) and all(
            _match(a, b) for a, b in zip(left.items, right.items, strict=True)
        )
    if isinstance(left, DictV) and isinstance(right, DictV):
        return _match(Vec("general", left.keys), Vec("general", right.keys)) and _match(
            Vec("general", left.vals), Vec("general", right.vals)
        )
    if isinstance(left, TableV) and isinstance(right, TableV):
        return left.keys == right.keys and left.columns == right.columns and all(
            _match(Vec("general", a), Vec("general", b)) for a, b in zip(left.cols, right.cols, strict=True)
        )
    return False


def q_not(value: Value) -> Value:
    if isinstance(value, Vec):
        return vec_of([q_not(item) for item in value.items])
    if not isinstance(value, Atom):
        raise QError("type", "not")
    if value.null:
        return null("bool")
    if value.typ == "bool":
        return boolean(not bool(value.value))
    if value.typ in _NUMERIC:
        return boolean(_as_float(value) == 0.0)
    raise QError("type", "not")


def q_null(value: Value) -> Value:
    if isinstance(value, Vec):
        return vec_of([q_null(item) for item in value.items])
    if isinstance(value, Atom):
        return boolean(value.null)
    return boolean(False)


def q_neg(value: Value) -> Value:
    if isinstance(value, Vec):
        return vec_of([q_neg(item) for item in value.items])
    if not isinstance(value, Atom):
        raise QError("type", "neg")
    if value.null:
        return value
    if value.typ == "float":
        return float_(-_as_float(value))
    if value.typ in _INTS:
        return _num(Atom(value.typ, value= -_as_int(value) if value.typ != "bool" else (0 if value.value else 1)), value.typ if value.typ != "bool" else "long")
    raise QError("type", "neg")


def q_abs(value: Value) -> Value:
    if isinstance(value, Vec):
        return vec_of([q_abs(item) for item in value.items])
    if not isinstance(value, Atom):
        raise QError("type", "abs")
    if value.null:
        return value
    if value.typ == "float":
        return float_(abs(_as_float(value)))
    if value.typ in _INTS and value.typ != "bool":
        return Atom(value.typ, value=wrap_int(value.typ, abs(_as_int(value))))
    if value.typ == "bool":
        return value
    raise QError("type", "abs")


def q_sqrt(value: Value) -> Value:
    if isinstance(value, Vec):
        return vec_of([q_sqrt(item) for item in value.items])
    if not isinstance(value, Atom) or value.typ not in _NUMERIC:
        raise QError("type", "sqrt")
    if value.null:
        return null("float")
    number = _as_float(value)
    if number < 0:
        raise QError("domain", "sqrt")
    return float_(math.sqrt(number))


def q_count(value: Value) -> Atom:
    if isinstance(value, Atom):
        return long(1)
    if isinstance(value, Vec):
        return long(len(value.items))
    if isinstance(value, DictV):
        return long(len(value.keys))
    if isinstance(value, TableV):
        return long(len(value.cols[0]) if value.cols else 0)
    return long(1)


def q_til(value: Value) -> Vec:
    if not isinstance(value, Atom) or value.typ not in _INTS or value.null:
        raise QError("type", "til")
    number = _as_int(value)
    if number < 0:
        raise QError("domain", "til")
    return vec_of([long(i) for i in range(number)])


def _flat_atoms(value: Value) -> list[Atom] | None:
    if isinstance(value, Atom):
        return [value]
    if isinstance(value, Vec) and all(isinstance(item, Atom) for item in value.items):
        return [cast(Atom, item) for item in value.items]
    return None


def q_sum(value: Value) -> Value:
    if isinstance(value, Atom):
        return value
    if isinstance(value, DictV):
        return q_sum(Vec("general", value.vals))
    if not isinstance(value, Vec):
        raise QError("type", "sum")
    if value.items and any(not isinstance(item, Atom) for item in value.items):
        acc: Value = value.items[0]
        for item in value.items[1:]:
            acc = add(acc, item)
        return acc
    atoms = [cast(Atom, item) for item in value.items]
    if not atoms:
        return long(0)
    typ = atoms[0].typ
    if typ not in _NUMERIC:
        raise QError("type", "sum")
    if typ == "float" or typ == "real":
        total = 0.0
        for atom in atoms:
            if not atom.null:
                total += _as_float(atom)
        return float_(total)
    total_i = 0
    for atom in atoms:
        if not atom.null:
            total_i += _as_int(atom) if atom.typ != "bool" else (1 if atom.value else 0)
    out_typ = "long" if typ in {"bool", "long"} else typ
    if out_typ == "bool":
        out_typ = "int"
    return Atom(out_typ if out_typ in {"short", "int", "byte", "long"} else "long", value=wrap_int(out_typ if out_typ in {"short", "int", "byte", "long"} else "long", total_i))


def q_sums(value: Value) -> Value:
    if isinstance(value, Atom):
        return value
    if not isinstance(value, Vec):
        raise QError("type", "sums")
    acc: Value = long(0)
    out: list[Value] = []
    for item in value.items:
        piece: Value = item
        if isinstance(item, Atom) and item.null and item.typ in _NUMERIC:
            piece = long(0) if item.typ in _INTS else float_(0.0)
        acc = add(acc, piece)
        out.append(acc)
    return vec_of(out)


def q_avg(value: Value) -> Value:
    if isinstance(value, Atom):
        if value.null:
            return null("float")
        if value.typ not in _NUMERIC:
            raise QError("type", "avg")
        return float_(_as_float(value))
    if not isinstance(value, Vec):
        raise QError("type", "avg")
    if any(not isinstance(item, Atom) for item in value.items):
        raise QError("unsupported", "avg of nested lists is outside the supported subset")
    nums = [item for item in value.items if isinstance(item, Atom) and not item.null]
    if not nums:
        return null("float")
    return float_(sum(_as_float(atom) for atom in nums) / len(nums))


def _minmax(value: Value, pick_max: bool) -> Value:
    if isinstance(value, Atom):
        return value
    if not isinstance(value, Vec):
        raise QError("type", "min" if not pick_max else "max")
    if any(not isinstance(item, Atom) for item in value.items):
        raise QError("unsupported", "nested min/max is outside the supported subset")
    atoms = [item for item in value.items if isinstance(item, Atom) and not item.null]
    if not atoms:
        raise QError("domain", "min/max of an empty or all-null list is outside the supported subset")
    best = atoms[0]
    for atom in atoms[1:]:
        greater = _cmp_atom("gt", atom, best).value
        if pick_max and greater:
            best = atom
        if not pick_max and not greater and not _cmp_atom("eq", atom, best).value:
            best = atom
    return best


def q_min(value: Value) -> Value:
    return _minmax(value, False)


def q_max(value: Value) -> Value:
    return _minmax(value, True)


def q_first(value: Value) -> Value:
    if isinstance(value, Atom):
        return value
    if isinstance(value, Vec):
        if not value.items:
            typ = value.etype if value.etype != "general" else "long"
            return null(typ)
        return value.items[0]
    if isinstance(value, TableV):
        if not value.cols or not value.cols[0]:
            raise QError("length", "first")
        return DictV(
            tuple(symbol(name) for name in value.columns),
            tuple(column[0] for column in value.cols),
        )
    raise QError("type", "first")


def q_last(value: Value) -> Value:
    if isinstance(value, Atom):
        return value
    if isinstance(value, Vec):
        if not value.items:
            typ = value.etype if value.etype != "general" else "long"
            return null(typ)
        return value.items[-1]
    raise QError("type", "last")


def q_reverse(value: Value) -> Value:
    if isinstance(value, Atom):
        return value
    if isinstance(value, Vec):
        return Vec(value.etype, tuple(reversed(value.items)))
    raise QError("type", "reverse")


def _sort_key(atom: Atom, descending: bool) -> tuple[int, object]:
    # Nulls sort first on asc and last on desc.
    if atom.null:
        return (1 if descending else 0, 0)
    payload: object = atom.value
    if isinstance(payload, bool):
        payload = int(payload)
    return (0 if descending else 1, payload)


def q_asc(value: Value) -> Value:
    if isinstance(value, Atom):
        return value
    if not isinstance(value, Vec):
        raise QError("type", "asc")
    atoms = _atoms(value)
    ordered = sorted(atoms, key=lambda atom: _sort_key(atom, False))
    return Vec(value.etype, tuple(ordered))


def q_desc(value: Value) -> Value:
    if isinstance(value, Atom):
        return value
    if not isinstance(value, Vec):
        raise QError("type", "desc")
    return _desc(value)


def _desc(value: Vec) -> Vec:
    atoms = _atoms(value)

    def key(atom: Atom) -> tuple[int, float, str]:
        if atom.null:
            return (1, 0.0, "")
        if isinstance(atom.value, (int, float, bool)):
            return (0, -float(atom.value), "")
        return (0, 0.0, str(atom.value))

    # Symbols and chars need reverse alpha while numbers need numeric reverse.
    # Split the comparison properly.
    def better(atom: Atom) -> tuple[int, int, float, str]:
        if atom.null:
            return (1, 0, 0.0, "")
        if isinstance(atom.value, (int, float)) and not isinstance(atom.value, bool):
            return (0, 0, -float(atom.value), "")
        if isinstance(atom.value, bool):
            return (0, 0, -float(atom.value), "")
        return (0, 1, 0.0, "".join(chr(255 - ord(ch)) for ch in str(atom.value)))

    ordered = sorted(atoms, key=better)
    return Vec(value.etype, tuple(ordered))


def q_distinct(value: Value) -> Value:
    if isinstance(value, Atom):
        return vec_of([value])
    if not isinstance(value, Vec):
        raise QError("type", "distinct")
    seen: list[Value] = []
    for item in value.items:
        if not any(_match(item, prev) for prev in seen):
            seen.append(item)
    return vec_of(seen)


def q_where(value: Value) -> Vec:
    atoms = _atoms(value) if not isinstance(value, Atom) else [value]
    indexes: list[Atom] = []
    for index, atom in enumerate(atoms):
        if atom.null:
            continue
        if atom.typ == "bool":
            count = 1 if atom.value else 0
        elif atom.typ in _INTS:
            count = _as_int(atom)
            if count < 0:
                raise QError("domain", "where")
        else:
            raise QError("type", "where")
        indexes.extend(long(index) for _ in range(count))
    return vec_of(indexes)


def q_enlist(value: Value) -> Vec:
    return vec_of([value])


def q_raze(value: Value) -> Value:
    if isinstance(value, Atom):
        return value
    if isinstance(value, Vec):
        flat: list[Value] = []
        for item in value.items:
            if isinstance(item, Vec):
                flat.extend(item.items)
            else:
                flat.append(item)
        return vec_of(flat)
    raise QError("type", "raze")


def q_type(value: Value) -> Atom:
    if isinstance(value, Atom):
        return short(-TYPE_CODE[value.typ])
    if isinstance(value, Vec):
        if value.etype == "general":
            return short(0)
        return short(TYPE_CODE[value.etype])
    if isinstance(value, DictV):
        return short(99)
    if isinstance(value, TableV):
        return short(98)
    if isinstance(value, LambdaV):
        return short(100)
    if isinstance(value, ProjV):
        return short(104)
    raise QError("type", "type")


def q_string(value: Value) -> Value:
    if isinstance(value, Vec):
        return vec_of([q_string(item) for item in value.items])
    if not isinstance(value, Atom):
        raise QError("type", "string")
    if value.null:
        return vec_of([null("char")])
    if value.typ == "symbol":
        return _chars(str(value.value))
    if value.typ == "long":
        return _chars(str(value.value))
    if value.typ == "float":
        assert isinstance(value.value, float)
        if math.isinf(value.value):
            return _chars("0w" if value.value > 0 else "-0w")
        text = repr(value.value)
        return _chars(text)
    if value.typ == "bool":
        return _chars("1" if value.value else "0")
    if value.typ == "date":
        return _chars(str(value.value))
    if value.typ == "char":
        return _chars(str(value.value))
    raise QError("nyi", "string of " + value.typ)


def _chars(text: str) -> Vec:
    return vec_of([char(ch) for ch in text])


def q_fill(replacement: Value, target: Value) -> Value:
    if isinstance(target, Vec) and isinstance(replacement, Atom):
        return vec_of([q_fill(replacement, item) for item in target.items])
    if isinstance(target, Atom) and isinstance(replacement, Atom):
        if target.null:
            return replacement
        return target
    if isinstance(target, Vec) and isinstance(replacement, Vec):
        if len(target.items) != len(replacement.items):
            raise QError("length", "fill")
        return vec_of([q_fill(a, b) for a, b in zip(replacement.items, target.items, strict=True)])
    raise QError("type", "fill")


def q_join(left: Value, right: Value) -> Vec:
    def pieces(value: Value) -> list[Value]:
        if isinstance(value, Vec):
            return list(value.items)
        return [value]

    return vec_of(pieces(left) + pieces(right))


def q_take(count: Value, source: Value) -> Vec:
    if not isinstance(count, Atom) or count.typ not in _INTS or count.null:
        raise QError("type", "take")
    number = _as_int(count)
    if isinstance(source, Vec) and source.etype == "general":
        seq: list[Value] = list(source.items)
    elif isinstance(source, Atom):
        seq = [source]
    else:
        seq = list(source.items) if isinstance(source, Vec) else [source]
    if number == 0:
        etype = source.etype if isinstance(source, Vec) else (source.typ if isinstance(source, Atom) else "general")
        return Vec(etype, ())
    if not seq:
        raise QError("length", "take")
    size = abs(number)
    if number > 0:
        picked = [seq[i % len(seq)] for i in range(size)]
    else:
        start = (len(seq) - (size % len(seq))) % len(seq)
        picked = [seq[(start + i) % len(seq)] for i in range(size)]
    return vec_of(picked)


def q_drop(count: Value, source: Value) -> Value:
    if not isinstance(count, Atom) or count.typ not in _INTS or count.null:
        raise QError("type", "drop")
    if isinstance(source, Atom):
        source = vec_of([source])
    if not isinstance(source, Vec):
        raise QError("type", "drop")
    number = _as_int(count)
    items = list(source.items)
    if number >= 0:
        kept = items[number:]
    else:
        kept = items[:number] if abs(number) < len(items) else []
    if source.etype != "general" and all(isinstance(item, Atom) for item in kept):
        return Vec(source.etype, tuple(kept))
    return vec_of(kept)


def q_find(source: Value, needle: Value) -> Value:
    if isinstance(source, Atom) and isinstance(needle, Atom):
        raise QError("unsupported", "roll/deal (?) on atoms is non-deterministic and unsupported")
    if isinstance(needle, Vec) and not isinstance(source, Vec):
        return vec_of([q_find(source, item) for item in needle.items])
    if not isinstance(source, Vec):
        raise QError("type", "find")
    if isinstance(needle, Vec) and source.etype != "char":
        return vec_of([q_find(source, item) for item in needle.items])
    for index, item in enumerate(source.items):
        if _match(item, needle):
            return long(index)
    return long(len(source.items))


def q_in(left: Value, right: Value) -> Value:
    if isinstance(left, Vec):
        return vec_of([q_in(item, right) for item in left.items])
    if not isinstance(right, Vec):
        right = vec_of([right])
    return boolean(any(_match(left, item) for item in right.items))


def q_dict(keys: Value, vals: Value) -> DictV:
    if isinstance(keys, Atom):
        keys = vec_of([keys])
    if isinstance(vals, Atom):
        vals = vec_of([vals])
    if not isinstance(keys, Vec) or not isinstance(vals, Vec):
        raise QError("type", "dict")
    if len(keys.items) != len(vals.items):
        raise QError("length", "dict")
    return DictV(keys.items, vals.items)


def q_div(left: Value, right: Value) -> Value:
    return _intdiv(left, right, mod=False)


def q_mod(left: Value, right: Value) -> Value:
    return _intdiv(left, right, mod=True)


def _intdiv(left: Value, right: Value, *, mod: bool) -> Value:
    if isinstance(left, Vec) or isinstance(right, Vec):
        return atomic_like(lambda a, b: _intdiv(a, b, mod=mod), left, right)
    if not isinstance(left, Atom) or not isinstance(right, Atom):
        raise QError("type", "div")
    if left.null or right.null:
        return null("long")
    if left.typ not in _INTS or right.typ not in _INTS:
        raise QError("type", "div")
    lv = _as_int(left)
    rv = _as_int(right)
    if lv < 0 or rv < 0:
        raise QError("domain", "negative div/mod is outside the supported subset")
    if rv == 0:
        raise QError("domain", "div zero")
    if mod:
        return long(lv % rv)
    return long(lv // rv)


def atomic_like(fn: Callable[[Value, Value], Value], left: Value, right: Value) -> Value:
    if isinstance(left, Vec) and isinstance(right, Atom):
        return vec_of([fn(item, right) for item in left.items])
    if isinstance(left, Atom) and isinstance(right, Vec):
        return vec_of([fn(left, item) for item in right.items])
    if isinstance(left, Vec) and isinstance(right, Vec):
        if len(left.items) != len(right.items):
            raise QError("length", "length")
        return vec_of([fn(a, b) for a, b in zip(left.items, right.items, strict=True)])
    return fn(left, right)


def q_flip(value: Value) -> Value:
    if isinstance(value, DictV):
        if not value.keys or not all(isinstance(key, Atom) and key.typ == "symbol" for key in value.keys):
            raise QError("type", "flip")
        names = [str(cast(Atom, key).value) for key in value.keys]
        columns: list[list[Atom]] = []
        width: int | None = None
        for val in value.vals:
            atoms = _atoms(val) if not isinstance(val, Atom) else [val]
            if isinstance(val, Atom):
                if width is None:
                    raise QError("length", "flip atom column")
                atoms = [val] * width
            if width is None:
                width = len(atoms)
            elif len(atoms) != width:
                raise QError("length", "flip")
            columns.append(atoms)
        if width is None:
            raise QError("length", "flip")
        return table_from_columns(names, columns)
    if isinstance(value, TableV):
        keys = tuple(symbol(name) for name in value.columns)
        vals = tuple(Vec(dict(value.types)[name], column) for name, column in zip(value.columns, value.cols, strict=True))
        return DictV(keys, vals)
    raise QError("type", "flip")


def make_list(items: Sequence[Value]) -> Vec:
    return vec_of(list(items))


def empty(etype: str) -> Vec:
    return Vec(etype, ())


def timestamp(year: int, month: int, day: int, hour: int, minute: int, second: int, micro: int = 0) -> Atom:
    import datetime as dt

    return Atom("timestamp", value=dt.datetime(year, month, day, hour, minute, second, micro))


def month(year: int, month_number: int) -> Atom:
    return Atom("month", value=(year, month_number))


class HoleV:
    pass


HOLE = HoleV()


def hole() -> HoleV:
    return HOLE


def call(value: Value, args: Sequence[Value | HoleV], env: Env | None = None) -> Value:
    env = env or Env()
    if any(isinstance(arg, HoleV) for arg in args):
        concrete = [None if isinstance(arg, HoleV) else arg for arg in args]
        if isinstance(value, LambdaV):
            bound: list[Value | None] = list(concrete) + [None] * max(0, len(value.params) - len(concrete))
            return ProjV(value, tuple(bound[: len(value.params)]))
        if isinstance(value, TableV) and len(concrete) == 2:
            row, col = concrete
            if row is None and col is not None:
                return index(value, col)
            if col is None and row is not None:
                return index(value, row)
        raise QError("nyi", "elided index")
    return apply(value, [arg for arg in args if not isinstance(arg, HoleV)], env)


def make_table(pairs: Sequence[tuple[str, Value]], key_names: Sequence[str] = ()) -> TableV:
    names = [name for name, _ in pairs]
    raw = [value for _, value in pairs]
    list_lengths = [len(value.items) for value in raw if isinstance(value, Vec)]
    if not list_lengths:
        raise QError("length", "enlist at least one column to build a table")
    if len(set(list_lengths)) != 1:
        raise QError("length", "column length")
    width = list_lengths[0]
    columns: list[list[Atom]] = []
    for value in raw:
        if isinstance(value, Atom):
            columns.append([value] * width)
        elif isinstance(value, Vec):
            columns.append(_atoms(value) if value.items or value.etype != "general" else [])
            if value.etype == "general" and not all(isinstance(item, Atom) for item in value.items):
                raise QError("type", "table column")
            columns[-1] = [cast(Atom, item) for item in value.items]
        else:
            raise QError("type", "table column")
    # Preserve etype for empty columns.
    types = []
    cols: list[tuple[Atom, ...]] = []
    for name, value, column in zip(names, raw, columns, strict=True):
        if isinstance(value, Vec) and not value.items:
            types.append((name, value.etype if value.etype != "general" else "long"))
        elif column:
            types.append((name, column[0].typ))
        else:
            types.append((name, "long"))
        cols.append(tuple(column))
    return TableV(tuple(names), tuple(types), tuple(cols), tuple(key_names))


def _rows(table: TableV) -> int:
    return len(table.cols[0]) if table.cols else 0


def _columns(table: TableV) -> dict[str, list[Atom]]:
    data = {name: list(column) for name, column in zip(table.columns, table.cols, strict=True)}
    data.setdefault("i", [long(i) for i in range(_rows(table))])
    return data


def _mask(value: Value, width: int) -> list[bool]:
    if isinstance(value, Atom) and value.typ == "bool":
        return [bool(value.value) and not value.null] * width
    if isinstance(value, Vec):
        flags: list[bool] = []
        for item in value.items:
            if not isinstance(item, Atom) or item.typ != "bool":
                raise QError("type", "where")
            flags.append(bool(item.value) and not item.null)
        if len(flags) != width:
            raise QError("length", "where")
        return flags
    raise QError("type", "where")


def _conform(values: list[tuple[str, Value]]) -> TableV:
    lengths: list[int | None] = []
    for _, value in values:
        if isinstance(value, Atom):
            lengths.append(None)
        elif isinstance(value, Vec) and all(isinstance(item, Atom) for item in value.items):
            lengths.append(len(value.items))
        elif isinstance(value, Vec):
            lengths.append(len(value.items))
        else:
            raise QError("type", "select column")
    concrete = [item for item in lengths if item is not None]
    if not concrete:
        width = 1
    else:
        if len(set(concrete)) != 1:
            raise QError("length", "select columns")
        width = concrete[0]
    names: list[str] = []
    columns: list[list[Atom]] = []
    for name, value in values:
        if isinstance(value, Atom):
            columns.append([value] * width)
        elif isinstance(value, Vec):
            if all(isinstance(item, Atom) for item in value.items):
                columns.append([cast(Atom, item) for item in value.items])
            else:
                raise QError("rank", "nested select column is outside the simple select subset")
        else:
            raise QError("type", "select")
        names.append(name)
    return table_from_columns(names, columns)


ColFn = Callable[[Scope], Value]


def q_select(
    table: Value,
    columns: Sequence[tuple[str, ColFn]],
    where: ColFn | None,
    by: Sequence[tuple[str, ColFn]] | None,
    env: Env | None = None,
) -> Value:
    if not isinstance(table, TableV):
        raise QError("type", "select")
    data = _columns(table)
    width = _rows(table)
    if where is not None:
        mask = _mask(where(Scope(data, env)), width)
        table = filter_table(table, mask)
        data = _columns(table)
        width = _rows(table)
    if by:
        return _select_by(data, width, columns, by, env)
    scope = Scope(data, env)
    produced = [(name, fn(scope)) for name, fn in columns]
    return _conform(produced)


def _select_by(
    data: dict[str, list[Atom]],
    width: int,
    columns: Sequence[tuple[str, ColFn]],
    by: Sequence[tuple[str, ColFn]],
    env: Env | None,
) -> TableV:
    scope = Scope(data, env)
    key_vals = [(name, _as_column(fn(scope), width)) for name, fn in by]
    groups: dict[tuple[str, ...], list[int]] = {}
    for index in range(width):
        stamp = tuple(q_repr(column[index]) for _, column in key_vals)
        groups.setdefault(stamp, []).append(index)
    key_names = [name for name, _ in key_vals]
    out_keys: dict[str, list[Atom]] = {name: [] for name in key_names}
    out_cols: dict[str, list[Atom]] = {name: [] for name, _ in columns}
    nested = {name: False for name, _ in columns}
    for indexes in groups.values():
        for name, column in key_vals:
            out_keys[name].append(column[indexes[0]])
        sub = {name: [column[i] for i in indexes] for name, column in data.items() if name != "i"}
        sub["i"] = [data["i"][i] for i in indexes]
        subscope = Scope(sub, env)
        for name, fn in columns:
            value = fn(subscope)
            if isinstance(value, Atom):
                out_cols[name].append(value)
            else:
                nested[name] = True
                raise QError("unsupported", "nested group column is outside the supported by subset")
    names = key_names + [name for name, _ in columns]
    cols = [out_keys[name] for name in key_names] + [out_cols[name] for name, _ in columns]
    return table_from_columns(names, cols, key_names)


def _as_column(value: Value, width: int) -> list[Atom]:
    if isinstance(value, Atom):
        return [value] * width
    if isinstance(value, Vec) and len(value.items) == width and all(isinstance(item, Atom) for item in value.items):
        return [cast(Atom, item) for item in value.items]
    raise QError("length", "by")


def q_exec(
    table: Value,
    columns: Sequence[tuple[str, ColFn]],
    where: ColFn | None,
    env: Env | None = None,
) -> Value:
    selected = q_select(table, columns, where, None, env)
    if not isinstance(selected, TableV):
        return selected
    if len(selected.columns) != 1:
        keys = tuple(symbol(name) for name in selected.columns)
        vals = tuple(Vec(dict(selected.types)[name], column) for name, column in zip(selected.columns, selected.cols, strict=True))
        return DictV(keys, vals)
    column = selected.cols[0]
    if len(column) == 1 and _rows(selected) == 1:
        # Keep a one-row exec of a vector column as a one-item list only when the
        # expression itself was an atom. Atoms were replicated to one row.
        return column[0] if len(column) == 1 else vec_of(list(column))
    return vec_of(list(column))


def q_update(
    table: Value,
    columns: Sequence[tuple[str, ColFn]],
    where: ColFn | None,
    env: Env | None = None,
) -> TableV:
    if not isinstance(table, TableV):
        raise QError("type", "update")
    data = _columns(table)
    width = _rows(table)
    mask = _mask(where(Scope(data, env)), width) if where else [True] * width
    indexes = [i for i, flag in enumerate(mask) if flag]
    sub = {name: [column[i] for i in indexes] for name, column in data.items()}
    scope = Scope(sub, env)
    updated = {name: list(column) for name, column in zip(table.columns, table.cols, strict=True)}
    types = dict(table.types)
    for name, fn in columns:
        value = fn(scope)
        if isinstance(value, Atom):
            atoms = [value] * len(indexes)
        elif isinstance(value, Vec) and all(isinstance(item, Atom) for item in value.items):
            if len(value.items) != len(indexes):
                raise QError("length", "update")
            atoms = [cast(Atom, item) for item in value.items]
        else:
            raise QError("type", "update")
        if name not in updated:
            blank = null(atoms[0].typ if atoms else "long")
            updated[name] = [blank] * width
        for index, atom in zip(indexes, atoms, strict=True):
            updated[name][index] = atom
        if atoms:
            types[name] = atoms[0].typ
    names = list(table.columns) + [name for name, _ in columns if name not in table.columns]
    return table_from_columns(names, [updated[name] for name in names])


def q_delete(
    table: Value,
    colnames: Sequence[str],
    where: ColFn | None,
    env: Env | None = None,
) -> TableV:
    if not isinstance(table, TableV):
        raise QError("type", "delete")
    if colnames and where is not None:
        raise QError("unsupported", "delete of columns combined with where is outside the supported subset")
    if where is not None:
        data = _columns(table)
        mask = _mask(where(Scope(data, env)), _rows(table))
        keep = [not flag for flag in mask]
        return filter_table(table, keep)
    drop = set(colnames)
    names = [name for name in table.columns if name not in drop]
    cols = [list(column) for name, column in zip(table.columns, table.cols, strict=True) if name not in drop]
    keys = [key for key in table.keys if key not in drop]
    return table_from_columns(names, cols, keys)


def q_cond(branches: Sequence[tuple[Callable[[], Value], Callable[[], Value]]], otherwise: Callable[[], Value]) -> Value:
    for test, result in branches:
        flag = test()
        if isinstance(flag, Vec):
            if len(flag.items) != 1:
                raise QError("type", "cond")
            flag = flag.items[0]
        if not isinstance(flag, Atom):
            raise QError("type", "cond")
        truthy = (not flag.null) and (
            (flag.typ == "bool" and bool(flag.value)) or (flag.typ in _NUMERIC and _as_float(flag) != 0.0)
        )
        if truthy:
            return result()
    return otherwise()


def lambda_(params: Sequence[str], call: Callable[[Env, tuple[Value, ...]], Value], label: str = "lambda") -> LambdaV:
    return LambdaV(tuple(params), len(params), call, label)


def _call_fn(fn: LambdaV | ProjV, args: Sequence[Value], env: Env) -> Value:
    if isinstance(fn, ProjV):
        return _call_proj(fn, args, env)
    if len(args) > len(fn.params):
        raise QError("rank", "too many arguments")
    if not fn.variadic and len(args) < len(fn.params):
        bound: list[Value | None] = list(args) + [None] * (len(fn.params) - len(args))
        return ProjV(fn, tuple(bound))
    local = env.child_global()
    return fn.call(local, tuple(args))


def _call_proj(proj: ProjV, args: Sequence[Value], env: Env) -> Value:
    bound = list(proj.bound)
    rest = list(args)
    for index, item in enumerate(bound):
        if item is None and rest:
            bound[index] = rest.pop(0)
    if rest:
        raise QError("rank", "too many arguments")
    if any(item is None for item in bound):
        return ProjV(proj.fn, tuple(bound))
    return _call_fn(proj.fn, [cast(Value, item) for item in bound], env)


def apply(value: Value, args: Sequence[Value], env: Env | None = None) -> Value:
    env = env or Env()
    if isinstance(value, (LambdaV, ProjV)):
        return _call_fn(value, args, env)
    if len(args) == 1:
        return index(value, args[0])
    if len(args) == 2 and isinstance(value, TableV):
        return _index_table(value, args[0], args[1])
    if len(args) == 2 and isinstance(value, Vec):
        return index(index(value, args[0]), args[1])
    raise QError("rank", "apply")


def index(value: Value, spec: Value) -> Value:
    if isinstance(spec, Vec):
        return vec_of([index(value, item) for item in spec.items])
    if isinstance(value, DictV):
        for key, val in zip(value.keys, value.vals, strict=True):
            if _match(key, spec):
                return val
        return null("long")
    if isinstance(value, TableV):
        if isinstance(spec, Atom) and spec.typ == "symbol":
            name = str(spec.value)
            if name not in value.columns:
                raise QError("name", name)
            column = value.cols[value.columns.index(name)]
            return Vec(dict(value.types)[name], column)
        if not isinstance(spec, Atom) or spec.null or spec.typ not in _INTS:
            raise QError("type", "index")
        row = _as_int(spec)
        width = _rows(value)
        if row < 0 or row >= width:
            return null("long")
        return DictV(tuple(symbol(name) for name in value.columns), tuple(column[row] for column in value.cols))
    if isinstance(value, Vec):
        if not isinstance(spec, Atom) or spec.null or spec.typ not in _INTS:
            raise QError("type", "index")
        pos = _as_int(spec)
        if pos < 0 or pos >= len(value.items):
            et = value.etype if value.etype != "general" else "long"
            return null(et)
        return value.items[pos]
    if isinstance(value, Atom):
        if not isinstance(spec, Atom) or spec.null or spec.typ not in _INTS:
            raise QError("type", "index")
        pos = _as_int(spec)
        if pos == 0:
            return value
        return null(value.typ)
    raise QError("type", "index")


def _index_table(table: TableV, row_spec: Value, col_spec: Value) -> Value:
    if isinstance(row_spec, Atom) and row_spec.null and isinstance(col_spec, Atom) and col_spec.typ == "symbol":
        return index(table, col_spec)
    if isinstance(col_spec, Atom) and col_spec.null:
        return index(table, row_spec)
    row_value = index(table, row_spec)
    if isinstance(col_spec, Atom) and col_spec.typ == "symbol" and isinstance(row_value, DictV):
        return index(row_value, col_spec)
    return row_value


def each(fn: Value, left: Value, right: Value | None, env: Env) -> Value:
    if right is None:
        items = left.items if isinstance(left, Vec) else (left,)
        return vec_of([apply(fn, [item], env) for item in items])
    if not isinstance(left, Vec) or not isinstance(right, Vec):
        raise QError("type", "each")
    if len(left.items) != len(right.items):
        raise QError("length", "each")
    return vec_of([apply(fn, [a, b], env) for a, b in zip(left.items, right.items, strict=True)])


def each_left(fn: Value, left: Value, right: Value, env: Env) -> Value:
    if not isinstance(left, Vec):
        left = vec_of([left])
    return vec_of([apply(fn, [item, right], env) for item in left.items])


def each_right(fn: Value, left: Value, right: Value, env: Env) -> Value:
    if not isinstance(right, Vec):
        right = vec_of([right])
    return vec_of([apply(fn, [left, item], env) for item in right.items])


def each_prior(fn: Value, source: Value, env: Env, init: Value | None = None) -> Value:
    if not isinstance(source, Vec):
        source = vec_of([source])
    items = list(source.items)
    if not items:
        return Vec(source.etype, ())
    out: list[Value] = []
    if init is None:
        out.append(items[0])
        previous = items[0]
        rest = items[1:]
    else:
        previous = init
        rest = items
    for current in rest:
        out.append(apply(fn, [current, previous], env))
        previous = current
    return vec_of(out)


def over(fn: Value, source: Value, env: Env, init: Value | None = None) -> Value:
    if not isinstance(source, Vec):
        source = vec_of([source])
    items = list(source.items)
    if init is None:
        if not items:
            raise QError("domain", "over")
        acc = items[0]
        rest = items[1:]
    else:
        acc = init
        rest = items
    for item in rest:
        acc = apply(fn, [acc, item], env)
    return acc


def scan(fn: Value, source: Value, env: Env, init: Value | None = None) -> Value:
    if not isinstance(source, Vec):
        source = vec_of([source])
    items = list(source.items)
    out: list[Value] = []
    if init is None:
        if not items:
            return Vec("general", ())
        acc = items[0]
        out.append(acc)
        rest = items[1:]
    else:
        acc = init
        rest = items
    for item in rest:
        acc = apply(fn, [acc, item], env)
        out.append(acc)
    return vec_of(out)


def do_times(times: Value, fn: Value, seed: Value, env: Env) -> Value:
    if not isinstance(times, Atom) or times.typ not in _INTS or times.null:
        raise QError("type", "do")
    count = _as_int(times)
    if count < 0:
        raise QError("domain", "do")
    acc = seed
    for _ in range(count):
        acc = apply(fn, [acc], env)
    return acc


_BIN = {
    "add": add,
    "sub": sub,
    "mul": mul,
    "div": div,
    "eq": eq,
    "ne": ne,
    "lt": lt,
    "gt": gt,
    "le": le,
    "ge": ge,
    "fill": q_fill,
    "join": q_join,
    "take": q_take,
    "drop": q_drop,
    "find": q_find,
    "dict": q_dict,
    "in": q_in,
    "div-int": q_div,
    "mod": q_mod,
}

_UNARY = {
    "neg": q_neg,
    "not": q_not,
    "null": q_null,
    "til": q_til,
    "count": q_count,
    "sum": q_sum,
    "sums": q_sums,
    "avg": q_avg,
    "min": q_min,
    "max": q_max,
    "first": q_first,
    "last": q_last,
    "reverse": q_reverse,
    "asc": q_asc,
    "desc": q_desc,
    "distinct": q_distinct,
    "where": q_where,
    "enlist": q_enlist,
    "raze": q_raze,
    "abs": q_abs,
    "sqrt": q_sqrt,
    "type": q_type,
    "string": q_string,
    "flip": q_flip,
}


def verb(op: str) -> LambdaV:
    if op in _BIN:
        fn = _BIN[op]

        def call_bin(env: Env, args: tuple[Value, ...]) -> Value:
            del env
            if len(args) != 2:
                raise QError("rank", op)
            return fn(args[0], args[1])

        return LambdaV(("x", "y"), 2, call_bin, op)
    if op in _UNARY:
        fnu = _UNARY[op]

        def call_un(env: Env, args: tuple[Value, ...]) -> Value:
            del env
            if len(args) != 1:
                raise QError("rank", op)
            return fnu(args[0])

        return LambdaV(("x",), 1, call_un, op)
    raise QError("nyi", op)


def derived(op: str, adverb: str) -> LambdaV:
    base = verb(op)

    def call(env: Env, args: tuple[Value, ...]) -> Value:
        if adverb == "each":
            if len(args) == 1:
                return each(base, args[0], None, env)
            if len(args) == 2:
                return each(base, args[0], args[1], env)
        if adverb == "each-left" and len(args) == 2:
            return each_left(base, args[0], args[1], env)
        if adverb == "each-right" and len(args) == 2:
            return each_right(base, args[0], args[1], env)
        if adverb == "each-prior":
            if len(args) == 1:
                return each_prior(base, args[0], env)
            if len(args) == 2:
                return each_prior(base, args[1], env, args[0])
        if adverb == "over":
            if len(args) == 1:
                return over(base, args[0], env)
            if len(args) == 2:
                return over(base, args[1], env, args[0])
        if adverb == "scan":
            if len(args) == 1:
                return scan(base, args[0], env)
            if len(args) == 2:
                return scan(base, args[1], env, args[0])
        raise QError("rank", adverb)

    return LambdaV(("x", "y"), 2, call, op + " " + adverb, True)


def display(value: Value) -> str:
    return q_repr(value)


def canon_value(value: Value) -> dict[str, object]:
    from q2py.values import canon

    return canon(value)
