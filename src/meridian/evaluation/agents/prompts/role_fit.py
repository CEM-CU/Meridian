"""Role-Fit Agent ("The Researcher") — system prompt + user prompt builder.

Evaluates whether each candidate's qualifications match the role requirements.
Primary consumer of CV-derived flags (EXPERIENCE_STRENGTH, EXPERIENCE_GAP).
Also evaluates personality-derived EXECUTION, STRATEGIC, and CULTURAL flags.
"""

import json

from meridian.common.sanitize import sanitize_for_prompt
from meridian.evaluation.agents._prompt_helpers import (
    build_candidate_section,
    build_flags_section,
    build_mode_preamble,
    build_output_schema_section,
    build_requirements_section,
    build_tensions_section,
)
from meridian.evaluation.layer1_signals import TensionPair
from meridian.models import CandidateData, Flag, Requirement

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

ROLE_FIT_SYSTEM_PROMPT = """You are The Researcher — the Role-Fit Evaluation Agent in a C-suite hiring pipeline.

YOUR MANDATE:
Evaluate whether each candidate's demonstrated qualifications match the role requirements.
You are the primary consumer of CV-derived evidence: rubric assessments, experience gaps,
and track record. You also evaluate personality-based EXECUTION, STRATEGIC, and CULTURAL signals
when available in full mode.

YOUR BOUNDARIES:
- You evaluate ONLY flags in your allowlist: EXECUTION, STRATEGIC, CULTURAL, EXPERIENCE_STRENGTH, EXPERIENCE_GAP.
- You do NOT comment on team dynamics, collision risk, complementarity, or derailment.
- You do NOT produce composite scores or rankings. Structure the evidence; do not pre-empt the decision.
- You do NOT override rubric levels set by Stage C. If the rubric assessed PARTIAL, cite it as PARTIAL.
- You interpret what a rubric level IMPLIES for the role — you do not reassess the rubric itself.

EVIDENCE CREDIBILITY HIERARCHY (highest to lowest):
1. scored_flag — from validated Big Five instrument. Highest credibility.
2. cv_rubric — structured rubric evaluation against a specific JD requirement. High credibility.
3. requirement_gap — confirmed absence of evidence after systematic CV search. High credibility.
4. biographical_pattern — career data interpretation. Medium credibility.
5. research_general — LLM inference from I/O psychology. Lowest credibility. CAP: 2 per agent.

CRITICAL RULES:
- Every claim must cite an evidence_basis with type and reference.
- For cv_rubric: reference = requirement_id (e.g., "REQ-04"). Do NOT override the rubric level.
- For requirement_gap: reference = requirement_id where no evidence was found.
- research_general cap: maximum 2 claims using this evidence type.
- Be specific. Cite the requirement. Cite the rubric level. State the implication.

OUTPUT: Return valid JSON matching the AgentVerdict schema. No prose outside the JSON.
"""


# ---------------------------------------------------------------------------
# User prompt builder
# ---------------------------------------------------------------------------


def build_role_fit_prompt(
    flags: list[Flag],
    tension_pairs: list[TensionPair],
    candidates: list[CandidateData],
    requirements: list[Requirement],
    assessment_modes: dict[str, str],
) -> tuple[str, str]:
    """Build (system_prompt, user_prompt) for the role-fit agent.

    Args:
        flags: Flags pre-filtered to ROLE_FIT_ALLOWLIST.
        tension_pairs: Full tension map from Layer 1 (agent filters to relevant).
        candidates: All candidate data (CV text excluded from prompts per spec).
        requirements: Confirmed JD requirement list.
        assessment_modes: Candidate name → "full" or "partial".

    Returns:
        Tuple of (system_prompt, user_prompt) strings.
    """
    sections = [
        build_mode_preamble(assessment_modes, agent_role="role_fit"),
        build_requirements_section(requirements),
        build_flags_section(flags, label="ROLE-FIT FLAGS (your mandate)"),
        build_tensions_section(tension_pairs),
        build_candidate_section(candidates),
        _build_task_section(candidates, assessment_modes),
        build_output_schema_section(agent_role="role_fit"),
    ]
    user_prompt = "\n\n".join(s for s in sections if s)
    return ROLE_FIT_SYSTEM_PROMPT, user_prompt


def _build_task_section(
    candidates: list[CandidateData],
    assessment_modes: dict[str, str],
) -> str:
    """Build the task instruction section for the role-fit agent."""
    candidate_names = [sanitize_for_prompt(c.name) for c in candidates]
    names_json = json.dumps(candidate_names)
    return f"""## YOUR TASK

For each candidate ({names_json}):

1. EXPERIENCE ASSESSMENT: Evaluate EXPERIENCE_STRENGTH and EXPERIENCE_GAP flags.
   - For each cv_rubric flag, state the requirement_id, the rubric level, and what it means for this role.
   - For each requirement_gap flag, state what is absent and why it matters.
   - Do NOT reinterpret the rubric level. Interpret its implications.

2. MANDATE ALIGNMENT: Evaluate EXECUTION, STRATEGIC, and CULTURAL flags (full mode only).
   - For each flag, state what capability it signals and how it connects to role requirements.

3. TENSION ACKNOWLEDGMENT: If tension pairs are listed, address the relevant ones.
   - Cross-stream tensions (positive CV + negative personality on same domain) require explicit comment.

4. For any PARTIAL-mode candidate: restrict claims to cv_rubric, requirement_gap, and biographical_pattern.
   Do not make personality-based claims.

Output exactly one AgentVerdict JSON object."""
