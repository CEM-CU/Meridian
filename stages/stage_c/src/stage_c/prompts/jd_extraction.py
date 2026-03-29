"""Prompt template for C1: JD requirement extraction.

Builds system and user prompts that instruct the LLM to extract discrete requirements
from a job description, assign assessability flags, and per-scenario priorities.
"""

from __future__ import annotations

from shared.sanitize import sanitize_for_prompt

REQUIREMENT_JSON_SCHEMA: str = """\
[
  {
    "requirement_id": "REQ-01",
    "text": "string (max 200 chars) — normalized requirement statement",
    "source_quote": "string (max 300 chars) — verbatim or near-verbatim from JD",
    "assessable_from_cv": true,
    "scenario_priority": {
      "digital_transformation": "high | medium | low",
      "post_acquisition": "high | medium | low",
      "turnaround": "high | medium | low",
      "stabilization": "high | medium | low",
      "growth": "high | medium | low"
    }
  }
]
"""

_SYSTEM_PROMPT: str = (
    """\
You are a senior executive recruiter specializing in C-suite hiring. Your task is to \
extract every discrete, assessable requirement from a job description (JD).

## Instructions

1. **Extract every discrete requirement.** Each requirement must be a single, atomic \
condition that can be independently evaluated against a candidate's CV or profile.

2. **Decompose compound requirements.** If a JD bullet contains multiple conditions \
joined by "and", "or", commas, or semicolons, split them into separate requirements. \
Example: "10+ years experience AND P&L responsibility" → 2 separate entries.

3. **Extract implicit requirements.** Role descriptions, reporting structures, and \
context clues imply requirements. Example: "Reports to CEO with board exposure" implies \
a requirement for board-level communication capability.

4. **Reframe role descriptions as candidate requirements.** Convert "The CTO will lead \
digital transformation" into "Proven track record leading digital transformation \
initiatives".

5. **Ignore boilerplate.** Skip equal opportunity statements, company marketing copy, \
benefits descriptions, and generic legal disclaimers.

6. **Assign assessable_from_cv.** Set to `true` for requirements that can be verified \
from a CV (experience, qualifications, tenure, scope). Set to `false` for behavioral, \
interpersonal, leadership style, or cultural fit requirements that require interview or \
psychometric assessment.

7. **Assign scenario_priority.** For each requirement, assign a priority (high, medium, \
or low) under each of the 5 leadership scenarios:
   - **digital_transformation**: Leading technology-driven business model change. \
Priorities: tech vision, change management, innovation track record.
   - **post_acquisition**: Integrating acquired companies or being integrated. \
Priorities: integration experience, cultural bridging, stakeholder management.
   - **turnaround**: Rescuing underperforming business units. \
Priorities: cost discipline, rapid decision-making, crisis leadership.
   - **stabilization**: Maintaining performance of a well-functioning unit. \
Priorities: operational excellence, team retention, process optimization.
   - **growth**: Scaling a business into new markets or segments. \
Priorities: market expansion, strategic partnerships, talent acquisition at scale.

8. **Target 8-15 requirements.** Fewer than 6 suggests the JD is too vague. More than \
18 suggests requirements need consolidation.

9. **Requirement text max 200 characters.** Must work as a column header in a trade-off \
matrix.

10. **Source quote max 300 characters.** Verbatim or near-verbatim from the JD.

11. **Sequential IDs.** Use REQ-01, REQ-02, ..., REQ-N.

## Output Format

Return ONLY a JSON array matching this schema (no markdown fences, no commentary):

"""
    + REQUIREMENT_JSON_SCHEMA
)

_USER_PROMPT_TEMPLATE: str = """\
Extract all discrete requirements from the following job description.

---
{jd_text}
---

Return the requirements as a JSON array. No additional text."""


def build_jd_extraction_prompt(jd_text: str) -> tuple[str, str]:
    """Build system and user prompts for JD extraction.

    Args:
        jd_text: Raw job description text.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    sanitized_jd = sanitize_for_prompt(jd_text)
    user_prompt = _USER_PROMPT_TEMPLATE.format(jd_text=sanitized_jd)
    return _SYSTEM_PROMPT, user_prompt
