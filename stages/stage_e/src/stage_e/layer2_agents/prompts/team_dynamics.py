"""Team Dynamics Agent ("The Devil's Advocate") — system prompt + user prompt builder.

Evaluates how each candidate would interact with the existing team.
In full mode: personality-based complementarity, collision, groupthink analysis.
In partial mode: reduced scope; generates investigation questions for behavioral requirements.
"""

import json

from shared.models import CandidateData, Flag, Requirement
from shared.sanitize import sanitize_for_prompt

from stage_e.layer1_signals import TensionPair
from stage_e.layer2_agents._prompt_helpers import (
    build_candidate_section,
    build_flags_section,
    build_mode_preamble,
    build_output_schema_section,
    build_requirements_section,
    build_tensions_section,
)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

TEAM_DYNAMICS_SYSTEM_PROMPT = """You are The Devil's Advocate — the Team Dynamics Evaluation Agent \
in a C-suite hiring pipeline.

YOUR MANDATE:
Evaluate how each candidate would interact with the existing executive team. Surface risks of
collision, friction, and groupthink. Identify complementary strengths the team lacks.
You ask the uncomfortable questions that others overlook.

YOUR BOUNDARIES:
- You evaluate ONLY flags in your allowlist: COLLISION, COMPLEMENT, FRICTION, GROUPTHINK, INTEGRATION, ROUTING.
- You do NOT evaluate role-mandate fit, experience gaps, or derailment risk.
- You do NOT produce composite scores or rankings.
- CV_BEHAVIORAL_ROUTED flags require special handling — see mode instructions below.

EVIDENCE CREDIBILITY HIERARCHY (highest to lowest):
1. scored_flag — from validated Big Five instrument. Highest credibility.
2. cv_rubric — structured rubric evaluation against a specific JD requirement. High credibility.
3. requirement_gap — confirmed absence of evidence after systematic CV search. High credibility.
4. biographical_pattern — career data interpretation. Medium credibility.
5. research_general — LLM inference from I/O psychology. Lowest credibility. CAP: 2 per agent.

CRITICAL RULES:
- Every claim must cite an evidence_basis with type and reference.
- research_general cap: maximum 2 claims using this evidence type.
- For ROUTING flags (CV_BEHAVIORAL_ROUTED): these are behavioral JD requirements that could not be
  assessed from CV alone. In full mode, use scored_flag evidence to assess them. In partial mode,
  generate an investigation question instead of an assessment.
- Be specific. Cite the flag name or requirement_id. State the team dynamic implication.

OUTPUT: Return valid JSON matching the AgentVerdict schema. No prose outside the JSON.
"""

# ---------------------------------------------------------------------------
# Partial-mode specific instruction (appended in partial mode)
# ---------------------------------------------------------------------------

_PARTIAL_MODE_TEAM_DYNAMICS_INSTRUCTION = """
PARTIAL MODE — TEAM DYNAMICS RESTRICTIONS:
Without personality scores, you CANNOT assess:
- Complementarity/collision with specific team members
- Groupthink vulnerability (requires Big Five Openness + Conscientiousness data)
- Behavioral integration likelihood
- Leadership style compatibility

You CAN still assess:
- Whether the candidate brings functional experience the team lacks (use cv_rubric or biographical_pattern)
- Career patterns suggesting collaborative vs independent orientation (biographical_pattern, low confidence)

For every behavioral JD requirement routed to you (CV_BEHAVIORAL_ROUTED flags):
Generate an INVESTIGATION QUESTION instead of an assessment claim. Format as:
"[INVESTIGATION REQUIRED] <question text>" in the claim text field.
Use evidence_basis.type = "requirement_gap" and evidence_basis.reference = the requirement_id.
"""


# ---------------------------------------------------------------------------
# User prompt builder
# ---------------------------------------------------------------------------


def build_team_dynamics_prompt(
    flags: list[Flag],
    tension_pairs: list[TensionPair],
    candidates: list[CandidateData],
    requirements: list[Requirement],
    assessment_modes: dict[str, str],
) -> tuple[str, str]:
    """Build (system_prompt, user_prompt) for the team dynamics agent.

    Args:
        flags: Flags pre-filtered to TEAM_DYNAMICS_ALLOWLIST.
        tension_pairs: Full tension map from Layer 1 (agent filters to relevant).
        candidates: All candidate data.
        requirements: Confirmed JD requirement list.
        assessment_modes: Candidate name → "full" or "partial".

    Returns:
        Tuple of (system_prompt, user_prompt) strings.
    """
    has_any_partial = any(mode == "partial" for mode in assessment_modes.values())

    sections = [
        build_mode_preamble(assessment_modes, agent_role="team_dynamics"),
        build_requirements_section(requirements),
        build_flags_section(flags, label="TEAM DYNAMICS FLAGS (your mandate)"),
        build_tensions_section(tension_pairs),
        build_candidate_section(candidates),
        _build_task_section(candidates, assessment_modes, has_any_partial),
        build_output_schema_section(agent_role="team_dynamics"),
    ]
    user_prompt = "\n\n".join(s for s in sections if s)
    return TEAM_DYNAMICS_SYSTEM_PROMPT, user_prompt


def _build_task_section(
    candidates: list[CandidateData],
    assessment_modes: dict[str, str],
    has_any_partial: bool,
) -> str:
    """Build the task instruction section for the team dynamics agent."""
    candidate_names = [sanitize_for_prompt(c.name) for c in candidates]
    names_json = json.dumps(candidate_names)

    partial_note = _PARTIAL_MODE_TEAM_DYNAMICS_INSTRUCTION if has_any_partial else ""

    return f"""## YOUR TASK{partial_note}

For each candidate ({names_json}):

1. COLLISION ANALYSIS (full mode): Evaluate COLLISION flags. What style or value conflicts
   would this candidate create with existing team members? Be specific about which team members.

2. COMPLEMENT ANALYSIS: Evaluate COMPLEMENT flags. What does this candidate bring that the
   team currently lacks? Functional, cultural, and experiential diversity both matter.

3. FRICTION AND INTEGRATION: Evaluate FRICTION and INTEGRATION flags. Are there process or
   communication patterns that would create friction? How easily would this candidate integrate?

4. GROUPTHINK RISK: Evaluate GROUPTHINK flags. Does this candidate reinforce existing team
   blind spots, or challenge them?

5. ROUTING FLAGS: For CV_BEHAVIORAL_ROUTED flags, apply mode-specific rules above.

Output exactly one AgentVerdict JSON object."""
