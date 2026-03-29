"""Shared text utilities for Stage C LLM response post-processing.

Provides common string manipulation helpers used across multiple Stage C modules.
No mutable state — every function takes typed inputs and returns typed outputs.
"""

from __future__ import annotations

import re

# Regex to strip markdown code fences (```json ... ``` or ``` ... ```).
_FENCE_PATTERN: re.Pattern[str] = re.compile(r"^```[^\n]*\n?|```\s*$", re.MULTILINE)


def strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences from LLM output.

    Handles both plain fences (``` ... ```) and language-tagged fences
    (```json ... ```, ```python ... ```, etc.).

    Args:
        text: Raw LLM output that may contain markdown code fences.

    Returns:
        Cleaned string with fences removed and surrounding whitespace stripped.
    """
    return _FENCE_PATTERN.sub("", text.strip()).strip()
