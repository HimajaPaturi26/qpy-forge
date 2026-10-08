# Security

Generated Python is executable. The studio treats it as untrusted.

## Threat model

The attacker controls the q source, and therefore the Python that the translator emits, and can also POST arbitrary Python to the validate path if they bypass the translator. The sandbox has to reject that Python before it runs. The defender is a single local user running the studio on their own machine. This is not a multi-tenant boundary.

What we try to stop:

- reading or writing arbitrary host files
- reading parent environment variables or secrets
- opening network connections
- starting processes
- importing modules
- calling `eval`, `exec`, `compile`, `open`, `globals`, or `locals`
- walking attributes to function globals, code objects, or frame objects
- using a subscript to reach `__builtins__`
- calling runtime helpers that are not part of the translator's API

## Local boundary

Two providers implement `SandboxProvider.run`:

- `SubprocessExecutor` is what the HTTP validate path uses.
- `InProcessExecutor` is what corpus scoring uses. It applies the same AST gate and the same runtime facade. It does not apply rlimits and it runs inside the studio process.

`validate_generated` allows only the AST shapes the code generator emits: a module, one `import q2py.runtime`, functions named `q2py_program` or `_lamN`, assignments, returns, calls, names, constants, lists, tuples, lambdas, `args[integer]`, and unary minus. Other syntax is rejected, including `import` of anything else, `from ... import`, f-strings, binary operators, dictionaries, and subscripts on anything but `args`.

Calls must be attribute calls or lambdas. Names such as `open`, `eval`, `exec`, `compile`, `globals`, `locals`, `getattr`, `os`, `sys`, `subprocess`, `socket`, and `importlib` are rejected, as are dunder names. Attributes may only be `q.<safe name>`, `env.get` / `env.set` / `env.set_global`, and `scope.get`. Nested attributes are rejected, which blocks `q.long.__globals__`. Frame fields such as `f_globals` and `gi_frame` are rejected. The safe names are `SAFE_RUNTIME_NAMES` in `q2py.sandbox_api`. The executed namespace receives a `RuntimeFacade` with only those callables, not the runtime module.

Builtins in the executed namespace are only an `__import__` that raises. `True`, `False`, and `None` are keywords.

`SubprocessExecutor` starts `python -I`. The child environment is only `PYTHONNOUSERSITE`, `PYTHONDONTWRITEBYTECODE`, `LANG`, `LC_ALL`, and `HOME=/tmp`. The parent environment is not copied. `sandbox_main` puts the package on `sys.path` itself. The child sets `RLIMIT_CPU` to 3 seconds, `RLIMIT_AS` to 2.5 GB, and `RLIMIT_FSIZE` to 8 MB, and the parent waits at most 5 seconds. `setrlimit` failures are ignored where the platform does not support them. `RLIMIT_NPROC` is not set to zero: on Linux that limit counts threads, and Polars cannot import without worker threads. Fork is therefore not stopped by an rlimit.

The runtime and value modules do not import `os`, `socket`, `subprocess`, or `importlib`. Polars is imported by the value model for table filters. Generated code cannot name that module.

## What this does not claim

This subprocess is not a container, a VM, a seccomp jail, or a separate network namespace. If a bug skips the AST gate, the child can still open host files the OS permits, connect to the network, and read anything already in its own address space. The in-process scorer shares the studio process, so the same bug there would see the parent environment.

Do not expose the validate endpoint to untrusted tenants without replacing `SubprocessExecutor` with a `SandboxProvider` that uses a container or VM.

No external model API is called. No license file is read or stored.
