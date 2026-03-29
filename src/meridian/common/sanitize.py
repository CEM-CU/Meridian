"""Input sanitization for LLM prompt injection prevention (F18).

Strips known prompt injection patterns from string inputs before they
are interpolated into LLM prompts. Fail-open: if sanitization encounters
an error, return the original text and log a warning.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Compiled patterns (module-level, immutable)
# ---------------------------------------------------------------------------

# Role injection: lines beginning with known role labels (case-insensitive)
_ROLE_LINE_PATTERN: re.Pattern[str] = re.compile(
    r"^[ \t]*(system|assistant|user|human|ai)\s*:.*$",
    re.IGNORECASE | re.MULTILINE,
)

# Override instruction phrases (case-insensitive, anywhere in text)
_OVERRIDE_PHRASES: tuple[str, ...] = (
    "ignore previous instructions",
    "ignore all instructions",
    "disregard above",
    "disregard all previous",
    "forget previous instructions",
    "forget all instructions",
)
_OVERRIDE_PATTERN: re.Pattern[str] = re.compile(
    "|".join(re.escape(phrase) for phrase in _OVERRIDE_PHRASES),
    re.IGNORECASE,
)

# Triple backtick blocks (``` ... ```)
_BACKTICK_BLOCK_PATTERN: re.Pattern[str] = re.compile(
    r"```[\s\S]*?```",
    re.MULTILINE,
)

# Sequences of three or more dashes (delimiter injection)
_DASH_SEQUENCE_PATTERN: re.Pattern[str] = re.compile(r"-{3,}")

# XML-like system/instruction tags
_SYSTEM_TAG_PATTERN: re.Pattern[str] = re.compile(
    r"</?(?:system|instructions?|prompt|context|override|cv_text)\b[^>]*>",
    re.IGNORECASE,
)

# Excessive whitespace: 3+ consecutive newlines → 2 newlines
_EXCESS_NEWLINE_PATTERN: re.Pattern[str] = re.compile(r"\n{3,}")

# Excessive spaces (not newlines): 3+ consecutive spaces → 1 space
_EXCESS_SPACE_PATTERN: re.Pattern[str] = re.compile(r" {3,}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def sanitize_for_prompt(text: str, max_length: int = 50_000) -> str:
    """Sanitize text for safe LLM prompt interpolation.

    Strips:
    - Common prompt injection delimiters and override instructions
    - Markdown/XML-like structures that could break prompt boundaries
    - Excessive whitespace sequences
    - Truncates to max_length

    Returns sanitized text. Does NOT raise — fail-open with logging.

    Args:
        text: Raw input text to sanitize.
        max_length: Maximum character length after sanitization. Defaults to 50_000.

    Returns:
        Sanitized text, always a str, never raises.
    """
    try:
        return _apply_sanitization(text, max_length)
    except Exception:
        logger.warning(
            "sanitize_for_prompt encountered an error; returning original text. text_length=%d",
            len(text),
            exc_info=True,
        )
        return text


# ---------------------------------------------------------------------------
# Internal implementation
# ---------------------------------------------------------------------------


def _apply_sanitization(text: str, max_length: int) -> str:
    """Apply all sanitization rules in order and return the cleaned text."""
    # 1. Strip role injection lines
    result = _ROLE_LINE_PATTERN.sub("", text)

    # 2. Neutralize override instruction phrases
    result = _OVERRIDE_PATTERN.sub("[redacted]", result)

    # 3. Remove triple backtick blocks
    result = _BACKTICK_BLOCK_PATTERN.sub("", result)

    # 4. Collapse triple+ dash sequences to a single dash
    result = _DASH_SEQUENCE_PATTERN.sub("-", result)

    # 5. Strip XML-like system/instruction tags
    result = _SYSTEM_TAG_PATTERN.sub("", result)

    # 6. Normalise excessive whitespace
    result = _EXCESS_NEWLINE_PATTERN.sub("\n\n", result)
    result = _EXCESS_SPACE_PATTERN.sub(" ", result)

    # 7. Truncate to max_length
    if len(result) > max_length:
        result = result[:max_length]

    return result
