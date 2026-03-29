"""E7 trade-off statement -- the single LLM call in the synthesis layer.

Produces a 2-4 sentence statement summarising the cross-candidate comparison.
Strictly constrained: no new analysis, references only structured input.
F18 sanitization applied to all user-sourced text before prompt injection.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from meridian.common.sanitize import sanitize_for_prompt

if TYPE_CHECKING:
    from meridian.extraction.protocols import LLMClient

    from .models import CandidateSummary, TradeOffCell

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a neutral synthesis agent producing a structured hiring decision brief.
Your task is to write a 2-4 sentence trade-off statement comparing candidates.

Rules:
- Reference ONLY the structured data provided in the user message.
- Do NOT introduce new analysis, inferences, or data not present in the input.
- Do NOT recommend a single candidate or pre-empt the committee's judgment.
- Write in clear, formal prose suitable for a C-suite audience.
- Output ONLY the trade-off statement -- no preamble, no labels, no JSON.
"""

_MAX_MATRIX_CHARS = 8_000
_MAX_SUMMARY_CHARS = 4_000

_FALLBACK_STATEMENT = (
    "Trade-off statement could not be generated. "
    "Please review the trade-off matrix directly for candidate comparison."
)


def _format_matrix_for_prompt(matrix: list[TradeOffCell]) -> str:
    """Serialise the trade-off matrix to a compact JSON string for the prompt."""
    rows = [
        {
            "requirement": sanitize_for_prompt(cell.requirement_text),
            "priority": cell.active_priority,
            "candidate": sanitize_for_prompt(cell.candidate_name),
            "rubric_level": cell.rubric_level,
            "confidence": cell.confidence,
        }
        for cell in matrix
    ]
    raw = json.dumps(rows, indent=2)
    # Truncate if oversized to stay within token budget.
    return raw[:_MAX_MATRIX_CHARS]


def _format_summaries_for_prompt(summaries: list[CandidateSummary]) -> str:
    """Serialise candidate summaries to a compact JSON string for the prompt."""
    rows = [
        {
            "candidate": sanitize_for_prompt(summary.candidate_name),
            "assessment_mode": summary.assessment_mode,
            "agent_highlights": {role: sanitize_for_prompt(text) for role, text in summary.agent_highlights.items()},
            "contested_signal_count": len(summary.contested_signals),
        }
        for summary in summaries
    ]
    raw = json.dumps(rows, indent=2)
    return raw[:_MAX_SUMMARY_CHARS]


async def generate_trade_off_statement(
    matrix: list[TradeOffCell],
    candidate_summaries: list[CandidateSummary],
    llm_client: LLMClient,
) -> str:
    """Generate 2-4 sentence trade-off statement via 1 LLM call.

    Strictly constrained: no new analysis, references only structured input.
    All user-sourced text is sanitized before prompt injection (F18).

    Args:
        matrix: The assembled trade-off matrix (Layer 1 output).
        candidate_summaries: Per-candidate Layer 2 summaries.
        llm_client: LLM client conforming to the LLMClient protocol.

    Returns:
        2-4 sentence trade-off statement string.
    """
    matrix_json = _format_matrix_for_prompt(matrix)
    summaries_json = _format_summaries_for_prompt(candidate_summaries)

    user_message = (
        "TRADE-OFF MATRIX (requirement x candidate, sorted by priority):\n"
        f"{matrix_json}\n\n"
        "CANDIDATE SUMMARIES (agent highlights per candidate):\n"
        f"{summaries_json}\n\n"
        "Write a 2-4 sentence trade-off statement comparing the candidates. "
        "Reference only the structured data above. Do not introduce new analysis."
    )

    logger.debug("Calling LLM for trade-off statement (%d chars input)", len(user_message))
    try:
        result = await llm_client.complete(system=_SYSTEM_PROMPT, user=user_message)
    except Exception:
        logger.warning("LLM call for trade-off statement failed; returning fallback.", exc_info=True)
        return _FALLBACK_STATEMENT

    stripped = result.strip()
    if not stripped:
        logger.warning("LLM returned empty trade-off statement; returning fallback.")
        return _FALLBACK_STATEMENT

    logger.debug("Trade-off statement generated (%d chars)", len(stripped))
    return stripped
