"""Shared prompt-building helpers used by all three Layer 2 agent prompts.

These helpers produce consistently formatted prompt sections. All user-sourced
text (candidate names, CV citations, requirement text) passes through
sanitize_for_prompt before being interpolated into prompts (F18).
"""

import json

from shared.models import CandidateData, Flag, Requirement
from shared.sanitize import sanitize_for_prompt

from stage_e.layer1_signals import TensionPair

# ---------------------------------------------------------------------------
# Mode preamble
# ---------------------------------------------------------------------------


def build_mode_preamble(
    assessment_modes: dict[str, str],
    agent_role: str,
) -> str:
    """Build the mode-dependent preamble section.

    Full mode: all evidence types permitted.
    Partial mode: scored_flag not available; personality claims banned.
    """
    modes_display = {sanitize_for_prompt(name): mode for name, mode in assessment_modes.items()}
    modes_json = json.dumps(modes_display, indent=2)

    all_full = all(m == "full" for m in assessment_modes.values())
    any_partial = any(m == "partial" for m in assessment_modes.values())

    if all_full:
        evidence_section = (
            "AVAILABLE EVIDENCE TYPES (all permitted):\n"
            "  - scored_flag: from validated Big Five instrument (highest credibility)\n"
            "  - cv_rubric: structured rubric against a JD requirement (high credibility)\n"
            "  - requirement_gap: confirmed absence of evidence (high credibility)\n"
            "  - biographical_pattern: career data interpretation (medium credibility)\n"
            "  - research_general: LLM inference from I/O psychology (lowest, max 2)"
        )
    elif any_partial:
        evidence_section = (
            "AVAILABLE EVIDENCE TYPES (partial mode — personality data absent):\n"
            "  - cv_rubric: structured rubric against a JD requirement (high credibility)\n"
            "  - requirement_gap: confirmed absence of evidence (high credibility)\n"
            "  - biographical_pattern: career data interpretation (medium credibility)\n"
            "  - research_general: LLM inference from I/O psychology (lowest, max 2)\n"
            "  NOT AVAILABLE: scored_flag (no personality data)\n\n"
            "PARTIAL MODE RESTRICTIONS:\n"
            "  - Do NOT make personality-based claims.\n"
            "  - Do NOT infer leadership style or derailment risk from CV language.\n"
            "  - Do NOT guess at Big Five dimensions.\n"
            "  - For behavioral requirements: state 'requires personality data' explicitly."
        )
    else:
        evidence_section = (
            "AVAILABLE EVIDENCE TYPES (mixed modes — check per-candidate mode):\n"
            "  - scored_flag: only for FULL mode candidates\n"
            "  - cv_rubric: available for all candidates\n"
            "  - requirement_gap: available for all candidates\n"
            "  - biographical_pattern: available for all candidates\n"
            "  - research_general: available for all candidates (max 2 total)"
        )

    return f"## ASSESSMENT MODE\n\nAgent role: {agent_role}\nPer-candidate modes:\n{modes_json}\n\n{evidence_section}"


# ---------------------------------------------------------------------------
# Requirements section
# ---------------------------------------------------------------------------


def build_requirements_section(requirements: list[Requirement]) -> str:
    """Build the requirement list section for the prompt."""
    if not requirements:
        return "## JD REQUIREMENTS\n\n(none provided)"

    lines = ["## JD REQUIREMENTS\n"]
    for req in requirements:
        req_id = sanitize_for_prompt(req.requirement_id)
        text = sanitize_for_prompt(req.text)
        cv_flag = "CV-assessable" if req.assessable_from_cv else "behavioral"
        lines.append(f"- {req_id}: {text} [{cv_flag}]")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Flags section
# ---------------------------------------------------------------------------


def build_flags_section(flags: list[Flag], label: str = "FLAGS") -> str:
    """Build a structured flag list section for the prompt.

    All candidate-sourced text (citations, notes) is sanitized.
    """
    if not flags:
        return f"## {label}\n\n(no flags in your allowlist for these candidates)"

    lines = [f"## {label}\n"]
    for flag in flags:
        candidate = sanitize_for_prompt(flag.candidate_name)
        name = flag.name  # flag names are system-generated, not user input
        category = flag.category.value
        valence = flag.valence.value
        evidence_type = flag.evidence_type.value

        line = f"- [{candidate}] {name} | category={category} | valence={valence} | evidence={evidence_type}"

        if flag.requirement_id:
            req_id = sanitize_for_prompt(flag.requirement_id)
            line += f" | req={req_id}"
        if flag.rubric_level:
            rubric = sanitize_for_prompt(flag.rubric_level)
            line += f" | rubric_level={rubric}"
        if flag.cv_citation:
            citation = sanitize_for_prompt(flag.cv_citation)
            line += f' | citation="{citation}"'
        if flag.confidence:
            line += f" | confidence={flag.confidence}"
        if flag.big_five_source:
            line += f" | big_five_source={flag.big_five_source}"
        if flag.topic_keywords:
            keywords = ", ".join(sanitize_for_prompt(kw, max_length=50) for kw in flag.topic_keywords[:5])
            line += f" | keywords=[{keywords}]"

        lines.append(line)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tensions section
# ---------------------------------------------------------------------------


def build_tensions_section(tension_pairs: list[TensionPair]) -> str:
    """Build the tension map section for the prompt."""
    if not tension_pairs:
        return ""

    lines = ["## INTERPRETIVE TENSIONS\n"]
    for pair in tension_pairs:
        candidate = sanitize_for_prompt(pair.candidate_name)
        description = sanitize_for_prompt(pair.description)
        lines.append(
            f"- [{candidate}] {pair.tension_type.upper()}: "
            f"{pair.positive_flag} (+) vs {pair.negative_flag} (-) "
            f"[domain={pair.domain}] — {description}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Candidate section
# ---------------------------------------------------------------------------


def build_candidate_section(candidates: list[CandidateData]) -> str:
    """Build the candidate summary section for the prompt.

    NOTE: Raw cv_text is NOT included in the prompt (per spec — it is
    ground truth for F04 audit validation only, not agent input).
    Big Five scores included for full-mode candidates.
    """
    if not candidates:
        return "## CANDIDATES\n\n(none)"

    lines = ["## CANDIDATES\n"]
    for candidate in candidates:
        name = sanitize_for_prompt(candidate.name)
        lines.append(f"### {name}")

        if candidate.big_five:
            bf = candidate.big_five
            lines.append(f"  Big Five: O={bf.O:.2f}, C={bf.C:.2f}, E={bf.E:.2f}, A={bf.A:.2f}, N={bf.N:.2f}")
            if candidate.personality_source:
                source = sanitize_for_prompt(candidate.personality_source)
                lines.append(f"  Personality source: {source}")
        else:
            lines.append("  Big Five: NOT PROVIDED (partial mode)")

        if candidate.team_context:
            lines.append("  Team context:")
            for member in candidate.team_context:
                member_name = sanitize_for_prompt(member.name)
                member_role = sanitize_for_prompt(member.role)
                bf = member.big_five
                lines.append(
                    f"    - {member_name} ({member_role}): "
                    f"O={bf.O:.2f}, C={bf.C:.2f}, E={bf.E:.2f}, "
                    f"A={bf.A:.2f}, N={bf.N:.2f}"
                )
        lines.append("")  # blank line between candidates

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Output schema section
# ---------------------------------------------------------------------------

_AGENT_VERDICT_SCHEMA = {
    "agent_role": "<role_fit | team_dynamics | risk>",
    "assessment_mode": "<full | partial>",
    "summary": "<20-1000 char overall summary>",
    "claims": [
        {
            "candidate_name": "<name>",
            "text": "<10-500 char claim text>",
            "confidence": "<high | medium | low>",
            "evidence_basis": {
                "type": "<scored_flag | cv_rubric | requirement_gap | biographical_pattern | research_general>",
                "reference": "<flag_name OR requirement_id OR free-text>",
                "detail": "<optional additional context>",
            },
        }
    ],
    "unaddressed_flags": ["<flag_name — flags you received but chose not to address>"],
}


def build_output_schema_section(agent_role: str) -> str:
    """Build the output schema instruction section."""
    schema_copy = dict(_AGENT_VERDICT_SCHEMA)
    schema_copy["agent_role"] = agent_role
    schema_json = json.dumps(schema_copy, indent=2)
    return (
        "## REQUIRED OUTPUT FORMAT\n\n"
        "Return EXACTLY this JSON structure. No prose outside the JSON.\n\n"
        f"{schema_json}\n\n"
        "REMINDERS:\n"
        "- research_general cap: maximum 2 claims total per this agent response.\n"
        "- For cv_rubric: reference = requirement_id (e.g., 'REQ-04'). Do NOT override rubric level.\n"
        "- For requirement_gap: reference = requirement_id with no evidence found.\n"
        "- List any flags you received but did not address in unaddressed_flags.\n"
        "- summary must be 20-1000 characters.\n"
        "- Each claim text must be 10-500 characters."
    )
