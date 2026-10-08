"""The only runtime names generated Python is allowed to call.

The code generator and this set must move together. Anything else on
``q2py.runtime`` (modules, classes from the value model, helpers) stays
outside the sandbox namespace.
"""

from __future__ import annotations

SAFE_RUNTIME_NAMES: frozenset[str] = frozenset(
    {
        "Env",
        "add",
        "boolean",
        "byte",
        "call",
        "char",
        "date",
        "derived",
        "div",
        "empty",
        "eq",
        "float_",
        "ge",
        "gt",
        "hole",
        "int_",
        "iterate",
        "lambda_",
        "le",
        "long",
        "lt",
        "make_list",
        "make_table",
        "match",
        "month",
        "mul",
        "ne",
        "null",
        "q_abs",
        "q_asc",
        "q_all",
        "q_any",
        "q_avg",
        "q_ceiling",
        "q_cols",
        "q_cond",
        "q_count",
        "q_delete",
        "q_desc",
        "q_dev",
        "q_differ",
        "q_dict",
        "q_distinct",
        "q_div",
        "q_drop",
        "q_enlist",
        "q_except",
        "q_exec",
        "q_fill",
        "q_fills",
        "q_find",
        "q_first",
        "q_flip",
        "q_floor",
        "q_group",
        "q_iasc",
        "q_idesc",
        "q_in",
        "q_inter",
        "q_join",
        "q_key",
        "q_last",
        "q_max",
        "q_maxs",
        "q_med",
        "q_min",
        "q_mins",
        "q_mod",
        "q_neg",
        "q_next",
        "q_not",
        "q_null",
        "q_prd",
        "q_prds",
        "q_prev",
        "q_raze",
        "q_reverse",
        "q_rotate",
        "q_select",
        "q_signum",
        "q_sqrt",
        "q_string",
        "q_sum",
        "q_sums",
        "q_take",
        "q_til",
        "q_type",
        "q_union",
        "q_update",
        "q_value",
        "q_var",
        "q_where",
        "q_xbar",
        "short",
        "sub",
        "symbol",
        "timestamp",
        "verb",
    }
)


class RuntimeFacade:
    """Attribute access is restricted to ``SAFE_RUNTIME_NAMES``.

    Generated code is also rejected by the AST checker before it runs. The
    facade is the second gate if those two ever disagree.
    """

    __slots__ = ("_api",)

    def __init__(self, api: dict[str, object]) -> None:
        object.__setattr__(self, "_api", api)

    def __getattr__(self, name: str) -> object:
        api = object.__getattribute__(self, "_api")
        if name in api:
            return api[name]
        raise AttributeError(name)


def build_facade() -> RuntimeFacade:
    import q2py.runtime as runtime

    missing = [name for name in SAFE_RUNTIME_NAMES if not callable(getattr(runtime, name, None))]
    if missing:
        raise RuntimeError(f"sandbox API is missing callables: {', '.join(sorted(missing))}")
    api = {name: getattr(runtime, name) for name in SAFE_RUNTIME_NAMES}
    return RuntimeFacade(api)
