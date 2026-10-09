"""Vercel Python entrypoint. The application object stays in q2py.api."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("Q2PY_CORPUS", str(ROOT / "corpus" / "cases.json"))
os.environ.setdefault("Q2PY_DB", "/tmp/q2py.sqlite")

from q2py.api import app  # noqa: E402

__all__ = ["app"]
