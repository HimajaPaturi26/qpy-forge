# Type mapping

Most q values are Python objects. Polars is not required to represent them.

| q | Python | Notes |
| --- | --- | --- |
| boolean, byte, short, int, long | `Atom` with a Python `int` | Width wraps with two's complement, except byte which stays 0–255. |
| real, float | `Atom` with a Python `float` | Real is stored after a float32 round trip when a real literal is parsed. |
| char | `Atom` with a one-character string | Space is the null char. |
| symbol | `Atom` with a string and no backtick | |
| date | `datetime.date` | Adding a long uses `timedelta`. |
| timestamp | `datetime.datetime` | Partial. Arithmetic is not claimed. |
| month | `(year, month)` tuple | Partial. |
| null | `Atom(null=True)` | |
| list / strand | `Vec` of values | Homogeneous atoms keep an `etype`. Nested lists are `general`. |
| dictionary | `DictV` | |
| table | `TableV` plus `to_frame()` | Columns are Polars series. Symbols and chars are Utf8, with the q type kept on `TableV.types`. Dates are Polars dates. Timestamps are datetime. |
| lambda / projection | `LambdaV` / `ProjV` | Not JSON-compared as source text. Display uses a q-like rendering. |
| function result used in tests | canonical JSON from `canon()` | Comparison uses this JSON, not `repr`. |

`where` on a table uses `filter_table`, which builds a Polars frame, applies the boolean mask, and reads the columns back into `TableV`.
