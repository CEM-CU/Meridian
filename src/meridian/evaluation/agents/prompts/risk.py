"""Risk Agent ("The Risk Analyst") — system prompt + user prompt builder.

Evaluates derailment risk, dark-side concerns, experience gaps on high-priority
requirements as risk signals, and evidence quality issues as meta-risk.

In partial mode: limited to CV-derived risk signals only.
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

RISK_SYSTEM_PROMPT = """You are The Risk Analyst — the Risk Evaluation Agent in a C-suite hiring pipeline.

YOUR MANDATE:
Identify failure pathways. Surface derailment risks, dark-side tendencies, experience gaps
on critical requirements, and evidence quality concerns that should give the committee pause.
Your job is to present the downside case with specificity and evidence — not to recommend rejection.

YOUR BOUNDARIES:
- You evaluate ONLY flags in your allowlist: DERAILMENT, DARK_SIDE, TENURE, EXPERIENCE_GAP, EVIDENCE_QUALITY.
- You do NOT evaluate positive qualifications, team dynamics, or complementarity.
- You do NOT produce composite scores or rankings.
- You do NOT make personality-based claims in partial mode.
- Industry mismatch is surfaced via CV_GAP flags on industry-related requirements.
  The requirement text carries the context — read it carefully.

EVIDENCE CREDIBILITY HIERARCHY (highest to lowest):
1. scored_flag — from validated Big Five instrument. Highest credibility.
2. cv_rubric — structured rubric evaluation against a specific JD requirement. High credibility.
3. requirement_gap — confirmed absence of evidence after systematic CV search. High credibility.
4. biographical_pattern — career data interpretation. Medium credibility.
5. research_general — LLM inference from I/O psychology. Lowest credibility. CAP: 2 per agent.

CRITICAL RULES:
- Every claim must cite an evidence_basis with type and reference.
- For cv_rubric references: evidence_basis.reference = requirement_id. Do NOT override the rubric level.
- For requirement_gap references: reference = the requirement_id where no evidence was found.
- research_general cap: maximum 2 claims using this evidence type.
- EXPERIENCE_GAP flags: distinguish high-priority gaps (critical risk) from lower-priority gaps.
  The flag name encodes priority — cite it explicitly.
- For EVIDENCE_QUALITY flags: frame as meta-risk — the committee may be deciding on thin data.
- Be precise. "Risk" requires a mechanism — state what could go wrong and why.

OUTPUT: Return valid JSON matching the AgentVerdict schema. No prose outside the JSON.
"""

# ---------------------------------------------------------------------------
# Partial-mode specific instruction
# ---------------------------------------------------------------------------

_PARTIAL_MODE_RISK_INSTRUCTION = """
PARTIAL MODE — RISK ASSESSMENT RESTRICTIONS:
Without personality scores, you CANNOT assess:
- Derailment risk (requires Big Five Conscientiousness, Neuroticism data)
- Dark-side tendencies (requires personality instrument)
- Neuroticism under stress
- Interpersonal abrasion risk

You CAN still assess:
- Experience-mandate gaps as failure risk (EXPERIENCE_GAP flags, especially high-priority)
- Evidence quality concerns (EVIDENCE_QUALITY flags — committee deciding on thin data)
- Tenure pattern risks if tenure data is available from CV extraction

For DERAILMENT and DARK_SIDE flags: if no scored_flag evidence is available, state:
"Derailment/dark-side assessment requires personality data — not assessed in partial mode."
"""


# ---------------------------------------------------------------------------
# User prompt builder
# ---------------------------------------------------------------------------


def build_risk_prompt(
    flags: list[Flag],
    tension_pairs: list[TensionPair],
    candidates: list[CandidateData],
    requirements: list[Requirement],
    assessment_modes: dict[str, str],
) -> tuple[str, str]:
    """Build (system_prompt, user_prompt) for the risk agent.

    Args:
        flags: Flags pre-filtered to RISK_ALLOWLIST.
        tension_pairs: Full tension map from Layer 1 (agent filters to relevant).
        candidates: All candidate data.
        requirements: Confirmed JD requirement list.
        assessment_modes: Candidate name → "full" or "partial".

    Returns:
        Tuple of (system_prompt, user_prompt) strings.
    """
    has_any_partial = any(mode == "partial" for mode in assessment_modes.values())

    sections = [
        build_mode_preamble(assessment_modes, agent_role="risk"),
        build_requirements_section(requirements),
        build_flags_section(flags, label="RISK FLAGS (your mandate)"),
        build_tensions_section(tension_pairs),
        build_candidate_section(candidates),
        _build_task_section(candidates, assessment_modes, has_any_partial),
        build_output_schema_section(agent_role="risk"),
    ]
    user_prompt = "\n\n".join(s for s in sections if s)
    return RISK_SYSTEM_PROMPT, user_prompt


def _build_task_section(
    candidates: list[CandidateData],
    assessment_modes: dict[str, str],
    has_any_partial: bool,
) -> str:
    """Build the task instruction section for the risk agent."""
    candidate_names = [sanitize_for_prompt(c.name) for c in candidates]
    names_json = json.dumps(candidate_names)

    partial_note = _PARTIAL_MODE_RISK_INSTRUCTION if has_any_partial else ""

    return f"""## YOUR TASK{partial_note}

For each candidate ({names_json}):

1. DERAILMENT RISK (full mode only): Evaluate DERAILMENT flags. What personality-based failure
   mechanisms exist? Under what conditions? Cite the specific Big Five source (scored_flag).

2. DARK SIDE CONCERNS (full mode only): Evaluate DARK_SIDE flags. What counterproductive
   tendencies emerge under pressure? How do they interact with this specific role?

3. EXPERIENCE GAPS AS RISK: Evaluate EXPERIENCE_GAP flags. For high-priority gaps:
   state the requirement, the gap severity (rubric level), and the failure pathway.
   A gap on a low-priority requirement is informational; a gap on a high-priority requirement
   is a risk signal requiring explicit committee attention.

4. TENURE PATTERNS: Evaluate TENURE flags. Do career duration patterns suggest commitment
   risk or role mismatch patterns?

5. EVIDENCE QUALITY: Evaluate EVIDENCE_QUALITY flags. Where is the committee deciding on
   thin or unreliable data? Frame as meta-risk.

6. TENSION PAIRS: If cross-stream tensions show positive CV alongside negative personality
   on the same domain, address this explicitly — it is a genuine risk signal.

Output exactly one AgentVerdict JSON object."""
