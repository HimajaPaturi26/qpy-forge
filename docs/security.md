# Security

Generated Python is executable. The studio treats it as untrusted.

## Boundary

- `validate_generated` parses the module and allows only a small AST: imports of `q2py.runtime` (stripped before exec), function definitions, assignments, returns, calls, names, constants, and basic expressions. Imports of other modules, attributes that escape the runtime, and dunder names are rejected.
- Builtins available to the program are `True`, `False`, `None`, and a `__import__` that raises.
- `SubprocessExecutor` runs `python -I` so site and user modules are not imported. `PYTHONPATH` is set and ignored by that flag; `sandbox_main` inserts the package path itself.
- The child environment is a new dict: `PATH`, `PYTHONPATH`, `PYTHONNOUSERSITE`, `PYTHONDONTWRITEBYTECODE`, `LANG`, `LC_ALL`, and `HOME=/tmp`. Parent secrets are not copied.
- `RLIMIT_CPU` is 3 seconds, `RLIMIT_AS` is 2.5 GB, `RLIMIT_FSIZE` is 8 MB, and the parent waits at most 5 seconds. `setrlimit` failures are ignored so the process still runs on platforms without those limits.
- Network access is not granted by the runtime API. The process is not put in a separate network namespace. A future production provider should add a namespace or a separate sandbox implementation behind the `Executor` protocol.

## What this does not claim

This is a development sandbox. It does not defend against a hostile local user who can already run processes, and it does not use seccomp or a container runtime. Do not expose the validate endpoint to untrusted tenants without replacing `SubprocessExecutor`.

No external model API is called. No license file is read or stored.
