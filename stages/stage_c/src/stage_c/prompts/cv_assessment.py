"""Prompt template for C3: CV rubric assessment.

Builds system and user prompts that instruct the LLM to evaluate all CV-assessable
requirements for a single candidate in one batched call. Requirements are ordered by
priority (high first) to ensure quality degradation — if any — affects low-priority
assessments only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shared.sanitize import sanitize_for_prompt

if TYPE_CHECKING:
    from shared.models import Priority, Requirement

# ---------------------------------------------------------------------------
# JSON output schema reference
# ---------------------------------------------------------------------------

CV_ASSESSMENT_JSON_SCHEMA: str = """\
[
  {
    "requirement_id": "REQ-01",
    "candidate_name": "string — exact name of the candidate",
    "rubric_level": "exceeds | meets | partial | gap | not_assessable",
    "confidence": "high | medium | low",
    "cv_citation": "string | null — CV passage cited (REQUIRED for exceeds/meets/partial)",
    "cv_location": "string | null — role/section where citation appears (req. for exceeds/meets/partial)",
    "notes": "string | null — assessor notes, recency concerns, conflicts",
    "investigation_question": "string | null — specific question (REQUIRED for gap/partial/low-confidence)"
  }
]
"""

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT: str = """\
You are an expert executive recruiter performing a structured CV assessment. Your task is \
to evaluate a single candidate's CV against a list of discrete job requirements. You will \
assign a rubric level, confidence rating, and (where required) evidence citations and \
investigation questions.

## Rubric Levels — Strict Definitions

Assign EXACTLY ONE level per requirement. Do not interpret or soften these definitions.

**exceeds** — CV evidence clearly SURPASSES the requirement. The surplus must be unambiguous. \
"P&L $500M+ required, CV shows $1.2B standalone P&L" is EXCEEDS. \
"P&L $500M+ required, CV shows $520M" is MEETS, NOT exceeds.

**meets** — CV evidence satisfies the requirement as stated. Direct, clear match. \
No inference needed beyond reading the CV.

**partial** — Some evidence exists but with identifiable gaps. Related but not directly \
matching experience, or insufficient depth/duration. Your notes MUST explain specifically: \
(a) what IS present, and (b) what IS MISSING.

**gap** — No supporting evidence found in the CV. You searched the entire document and \
found nothing addressing this requirement. This is not a failure — it is the correct answer \
when evidence does not exist.

**not_assessable** — The requirement cannot be evaluated from CV data alone. Use exclusively \
for behavioral/interpersonal requirements and for requirements so vague that no CV evidence \
could meaningfully address them.

## Mandatory Citation Rule — CRITICAL

For **exceeds**, **meets**, and **partial**: you MUST provide a `cv_citation` (a specific \
verbatim or near-verbatim passage from the CV) AND a `cv_location` (role name, section, or \
paragraph reference). Omitting the citation for these levels is NOT permitted.

For **gap** and **not_assessable**: set `cv_citation` and `cv_location` to null.

## Confidence Tagging

Assign confidence based on the directness of the evidence:

**high** — Direct, unambiguous evidence. Explicit years, explicit team sizes, explicit \
revenue figures, named degrees.

**medium** — Evidence requires inference. "Led EMEA expansion" implies international scope \
but doesn't name countries. Title implies scope but isn't explicit.

**low** — Evidence is indirect or heavily interpretive. Candidate was present during a \
relevant event but their specific role is unclear. Title could mean different things \
across organisations.

## Investigation Question Rule

For every **gap**, **partial**, or **low**-confidence assessment: generate a specific, \
targeted investigation question that references both the requirement and the evidence gap. \
Do NOT write generic questions like "Can you describe your experience in this area?" \
Write specific questions like: "Clarify whether the EUR 480M divisional budget constituted \
standalone P&L ownership or was a cost centre within a larger business unit."

## Semantic Matching

Match by meaning, not keywords. If the JD says "transformation experience" and the CV \
says "organisational redesign," treat this as a semantic match. When the match is semantic \
rather than lexical, assign confidence MEDIUM (not HIGH).

## Edge Cases

- **Old experience:** Assign the appropriate level but note recency in the `notes` field.
- **Multiple conflicting passages:** Cite the MOST RELEVANT one; note conflicts in `notes`.
- **Same passage covers multiple requirements:** Cite it for each — this is correct.
- **Impossible requirement:** Assign gap and note in `notes` if the requirement appears to \
exceed industry timelines.
- **Very short CV:** Most requirements will be gap or low-confidence partial. This is \
correct behaviour.

## Output Format

Return ONLY a JSON array — one object per requirement, in the SAME ORDER as the \
requirements list provided. No markdown fences, no commentary, no preamble.

"""

_SYSTEM_PROMPT += "Schema:\n\n" + CV_ASSESSMENT_JSON_SCHEMA

# ---------------------------------------------------------------------------
# User prompt template
# ---------------------------------------------------------------------------

_USER_PROMPT_TEMPLATE: str = """\
Candidate: {candidate_name}

Requirements to assess (ordered by priority — high first):

{requirements_block}

Candidate CV:

<cv_text>
{cv_text}
</cv_text>

Assess the candidate against every requirement listed above. Return ONLY the JSON array. \
One object per requirement, in the same order. No additional text."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_requirements_block(
    priority_order: list[tuple[Requirement, Priority]],
) -> str:
    """Format the ordered requirements list for the prompt.

    Produces a numbered list with priority labels and requirement IDs.
    """
    lines: list[str] = []
    for idx, (req, priority) in enumerate(priority_order, start=1):
        sanitized_text = sanitize_for_prompt(req.text, max_length=200)
        lines.append(f"{idx}. [{priority.value.upper()}] {req.requirement_id}: {sanitized_text}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_cv_assessment_prompt(
    requirements: list[Requirement],
    candidate_name: str,
    cv_text: str,
    priority_order: list[tuple[Requirement, Priority]],
) -> tuple[str, str]:
    """Build system and user prompts for CV rubric assessment.

    Requirements are presented in the order specified by `priority_order` (high first),
    ensuring any LLM quality degradation at the end of long outputs affects only
    lower-priority assessments. CV text is sanitized before interpolation (F18).

    Args:
        requirements: Full list of Requirement objects (used for validation context).
        candidate_name: Exact candidate name to embed in the prompt.
        cv_text: Raw CV text. Will be sanitized before interpolation.
        priority_order: Ordered list of (Requirement, Priority) tuples, high priority first.
            This sequence controls the order requirements appear in the prompt.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    sanitized_cv = sanitize_for_prompt(cv_text)
    sanitized_name = sanitize_for_prompt(candidate_name, max_length=200)
    requirements_block = _format_requirements_block(priority_order)
    user_prompt = _USER_PROMPT_TEMPLATE.format(
        candidate_name=sanitized_name,
        requirements_block=requirements_block,
        cv_text=sanitized_cv,
    )
    return _SYSTEM_PROMPT, user_prompt
