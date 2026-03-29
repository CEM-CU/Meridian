"""Conftest for API tests — ensures local helpers are importable."""

from __future__ import annotations

import sys
from pathlib import Path

_API_TESTS_DIR = str(Path(__file__).resolve().parent)
if _API_TESTS_DIR not in sys.path:
    sys.path.insert(0, _API_TESTS_DIR)
