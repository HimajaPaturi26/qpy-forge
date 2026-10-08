"""Optional q/kdb+ oracle.

The core translator never requires q. When the `q` binary is absent, every
oracle result is the explicit status ``oracle-unavailable``.
"""

from __future__ import annotations

import os
import shutil
from typing import Any


def oracle_status() -> dict[str, Any]:
    binary = os.environ.get("Q2PY_Q_BIN") or shutil.which("q")
    if not binary:
        return {
            "available": False,
            "status": "oracle-unavailable",
            "reason": "q binary not found. Authored-value validation still runs.",
        }
    license_hint = os.environ.get("QHOME") or os.environ.get("QLIC")
    return {
        "available": True,
        "status": "available",
        "binary": binary,
        "license_env_present": bool(license_hint),
        "reason": "q was found. Oracle execution is not enabled in this build; comparison stays on authored values.",
    }


def oracle_check(source: str) -> dict[str, Any]:
    del source
    status = oracle_status()
    if not status["available"]:
        return {"match": None, "status": "oracle-unavailable", "reason": status["reason"]}
    return {
        "match": None,
        "status": "oracle-unavailable",
        "reason": "q was detected, but live oracle execution is intentionally not required and is not invoked.",
    }
