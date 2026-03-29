"""Layer 3 Audit — 8 deterministic checks on agent verdicts (E5).

Quality firewall between Layer 2 agent output and Layer 4 synthesis.
Zero LLM calls. All checks are pure functions: no mutation of inputs.
Checks may strip claims or add warnings but never block the pipeline.

Check 1: JSON Schema Validation
Check 2: Flag Scope Enforcement
Check 3: Unaddressed Flag Detection
Check 4: Hallucinated Flag/Reference Detection
Check 5: Biographical Reference Validation (F04) — STRONGEST check
Check 6: Semantic Drift Detection (F05)
Check 7: research_general Cap (F07)
Check 8: Downweight Ratio Warning (F14)
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from pydantic import ValidationError

from meridian.evaluation.layer0_validation import _ALL_FLAG_NAMES
from meridian.evaluation.schemas import AgentEvidenceType, AgentVerdict, Claim, validate_research_general_cap
from meridian.models.rubric import RubricLevel

if TYPE_CHECKING:
    from meridian.models.candidates import CandidateData
    from meridian.models.flags import Flag, FlagCategory
    from meridian.models.requirements import Requirement
    from meridian.models.rubric import RubricAssessment

logger = logging.getLogger(__name__)

# Gap/not_assessable rubric levels — used in Check 5
_GAP_LEVELS: frozenset[RubricLevel] = frozenset({RubricLevel.GAP, RubricLevel.NOT_ASSESSABLE})


# ---------------------------------------------------------------------------
# Check 1: JSON Schema Validation
# ---------------------------------------------------------------------------


def check_schema_validity(verdict: AgentVerdict) -> list[str]:
    """Re-validate verdict schema. Returns warnings for any issues.

    Pydantic validation already ran when the verdict was constructed. This
    re-validates the serialised form as a belt-and-suspenders check — catches
    any inconsistency introduced by in-memory manipulation between construction
    and audit.
    """
    warnings: list[str] = []
    try:
        AgentVerdict.model_validate(verdict.model_dump())
    except ValidationError as exc:
        for err in exc.errors():
            loc = " -> ".join(str(p) for p in err["loc"])
            warnings.append(f"[CHECK1] Schema re-validation failed for '{verdict.agent_role}': {loc}: {err['msg']}")
    return warnings


# ---------------------------------------------------------------------------
# Check 2: Flag Scope Enforcement
# ---------------------------------------------------------------------------


def check_flag_scope(
    verdict: AgentVerdict,
    agent_allowlist: frozenset[FlagCategory],
    available_flags: list[Flag],
) -> tuple[AgentVerdict, list[str]]:
    """Enforce that each claim only cites flags from the agent's allowlist.

    For scored_flag evidence: the cited flag must exist in available_flags AND
    its category must be in the allowlist. Out-of-scope claims are stripped.

    Args:
        verdict: The agent verdict to audit.
        agent_allowlist: FlagCategory values permitted for this agent role.
        available_flags: The full flag set passed to this audit run.

    Returns:
        A new AgentVerdict (stripped if necessary) and list of warning strings.
    """
    flag_category_map: dict[str, FlagCategory] = {f.name: f.category for f in available_flags}
    warnings: list[str] = []
    kept_claims: list[Claim] = []

    for claim in verdict.claims:
        if claim.evidence_basis.type != AgentEvidenceType.SCORED_FLAG:
            kept_claims.append(claim)
            continue

        flag_name = claim.evidence_basis.reference
        category = flag_category_map.get(flag_name)

        if category is None:
            # Flag name not in available flags — strip as out-of-scope.
            msg = (
                f"[CHECK2] Claim stripped from '{verdict.agent_role}': "
                f"scored_flag '{flag_name}' not found in available flags"
            )
            warnings.append(msg)
            logger.warning(msg)
            continue

        if category not in agent_allowlist:
            msg = (
                f"[CHECK2] Claim stripped from '{verdict.agent_role}': "
                f"flag '{flag_name}' (category={category}) is outside allowlist"
            )
            warnings.append(msg)
            logger.warning(msg)
        else:
            kept_claims.append(claim)

    if len(kept_claims) == len(verdict.claims):
        return verdict, warnings

    updated = verdict.model_copy(update={"claims": kept_claims})
    return updated, warnings


# ---------------------------------------------------------------------------
# Check 3: Unaddressed Flag Detection
# ---------------------------------------------------------------------------


def check_unaddressed_flags(
    verdict: AgentVerdict,
    agent_flags: list[Flag],
) -> list[str]:
    """Detect in-mandate flags that the agent silently dropped.

    Compares flags the agent received against flags cited in scored_flag claims.
    Any flag not cited is surfaced as an "unaddressed signal" warning.

    Does NOT strip claims — informational only.
    """
    cited_flag_names: frozenset[str] = frozenset(
        claim.evidence_basis.reference
        for claim in verdict.claims
        if claim.evidence_basis.type == AgentEvidenceType.SCORED_FLAG
    )

    warnings: list[str] = []
    for flag in agent_flags:
        if flag.name not in cited_flag_names:
            warnings.append(
                f"[CHECK3] Unaddressed signal in '{verdict.agent_role}': "
                f"flag '{flag.name}' (candidate='{flag.candidate_name}') not cited in any claim"
            )
    return warnings


# ---------------------------------------------------------------------------
# Check 4: Hallucinated Flag / Reference Detection
# ---------------------------------------------------------------------------


def check_hallucinated_references(
    verdict: AgentVerdict,
    valid_flag_names: frozenset[str],
    valid_requirement_ids: frozenset[str],
) -> tuple[AgentVerdict, list[str]]:
    """Strip claims with hallucinated flag names or requirement IDs.

    For scored_flag: reference must be in valid_flag_names.
    For cv_rubric / requirement_gap: reference must be in valid_requirement_ids.
    Other evidence types are not validated here.

    Args:
        verdict: Agent verdict to audit.
        valid_flag_names: Canonical flag vocabulary (from Layer 0).
        valid_requirement_ids: Confirmed requirement IDs from the requirement list.

    Returns:
        New AgentVerdict with hallucinated claims stripped, and warnings list.
    """
    warnings: list[str] = []
    kept_claims: list[Claim] = []

    for claim in verdict.claims:
        eb = claim.evidence_basis
        hallucinated = False

        if eb.type == AgentEvidenceType.SCORED_FLAG:
            if eb.reference not in valid_flag_names:
                warnings.append(
                    f"[CHECK4] Claim stripped from '{verdict.agent_role}': "
                    f"flag name '{eb.reference}' not in canonical vocabulary"
                )
                hallucinated = True

        elif (
            eb.type in (AgentEvidenceType.CV_RUBRIC, AgentEvidenceType.REQUIREMENT_GAP)
            and eb.reference not in valid_requirement_ids
        ):
            warnings.append(
                f"[CHECK4] Claim stripped from '{verdict.agent_role}': "
                f"requirement_id '{eb.reference}' not in confirmed requirement list"
            )
            hallucinated = True

        if not hallucinated:
            kept_claims.append(claim)

    if len(kept_claims) == len(verdict.claims):
        return verdict, warnings

    updated = verdict.model_copy(update={"claims": kept_claims})
    return updated, warnings


# ---------------------------------------------------------------------------
# Check 5 (F04): Biographical Reference Validation — STRONGEST CHECK
# ---------------------------------------------------------------------------


def _normalise_text(text: str) -> str:
    """Lowercase and collapse whitespace for substring matching."""
    return re.sub(r"\s+", " ", text.lower()).strip()


def _cv_text_for_candidate(
    candidate_name: str,
    candidate_data: list[CandidateData],
) -> str | None:
    """Return normalised CV text for a candidate, or None if not found."""
    normalised_target = _normalise_text(candidate_name)
    for candidate in candidate_data:
        if _normalise_text(candidate.name) == normalised_target:
            return _normalise_text(candidate.cv_text)
    return None


def _rubric_for(
    requirement_id: str,
    candidate_name: str,
    rubric_assessments: list[RubricAssessment],
) -> RubricAssessment | None:
    """Return the rubric assessment for a requirement x candidate pair."""
    for assessment in rubric_assessments:
        if assessment.requirement_id == requirement_id and assessment.candidate_name == candidate_name:
            return assessment
    return None


def _check_cv_rubric_claim(
    claim: Claim,
    candidate_data: list[CandidateData],
    rubric_assessments: list[RubricAssessment],
) -> str | None:
    """Validate a cv_rubric claim. Returns a warning string if invalid, else None."""
    req_id = claim.evidence_basis.reference
    rubric = _rubric_for(req_id, claim.candidate_name, rubric_assessments)

    if rubric is None:
        return (
            f"[CHECK5] cv_rubric claim stripped from '{claim.candidate_name}': "
            f"no rubric assessment found for requirement '{req_id}'"
        )

    # If the claim cites a CV passage in its detail field, validate it against
    # the raw CV text (citation fabrication detection).
    if claim.evidence_basis.detail:
        cv_text = _cv_text_for_candidate(claim.candidate_name, candidate_data)
        if cv_text is not None:
            normalised_detail = _normalise_text(claim.evidence_basis.detail)
            if normalised_detail and normalised_detail not in cv_text:
                return (
                    f"[CHECK5] cv_rubric claim stripped from '{claim.candidate_name}': "
                    f"cited passage not found in raw CV text for requirement '{req_id}'"
                )

    return None


def _check_requirement_gap_claim(
    claim: Claim,
    rubric_assessments: list[RubricAssessment],
    requirements: list[Requirement],
) -> str | None:
    """Validate a requirement_gap claim. Returns a warning string if invalid, else None."""
    req_id = claim.evidence_basis.reference

    # Verify the requirement exists (hallucinated references caught in Check 4,
    # but double-check here for belt-and-suspenders).
    req_exists = any(r.requirement_id == req_id for r in requirements)
    if not req_exists:
        return (
            f"[CHECK5] requirement_gap claim stripped from '{claim.candidate_name}': "
            f"requirement_id '{req_id}' not in confirmed list"
        )

    # Behavioral requirements (assessable_from_cv=False) have no rubric by design.
    # Agents may cite them as requirement_gap to note the routing — this is valid.
    req_obj = next((r for r in requirements if r.requirement_id == req_id), None)
    if req_obj is not None and not req_obj.assessable_from_cv:
        return None  # Behavioral requirement — no rubric to validate against, claim is valid.

    rubric = _rubric_for(req_id, claim.candidate_name, rubric_assessments)
    if rubric is None:
        return (
            f"[CHECK5] requirement_gap claim stripped from '{claim.candidate_name}': "
            f"no rubric assessment found for requirement '{req_id}' to verify gap"
        )

    if rubric.rubric_level not in _GAP_LEVELS:
        return (
            f"[CHECK5] requirement_gap claim stripped from '{claim.candidate_name}': "
            f"rubric for '{req_id}' is '{rubric.rubric_level}' (not gap/not_assessable) — "
            f"misrepresentation of evidence"
        )

    return None


def check_biographical_references(
    verdict: AgentVerdict,
    candidate_data: list[CandidateData],
    rubric_assessments: list[RubricAssessment],
    requirements: list[Requirement],
) -> tuple[AgentVerdict, list[str]]:
    """Validate cv_rubric and requirement_gap citations (F04).

    For cv_rubric: verifies requirement resolves to an actual rubric assessment.
    If the claim's detail field contains a CV passage, verifies that passage
    appears in the raw CV text (citation fabrication detection).

    For requirement_gap: verifies the requirement exists AND the rubric assessment
    for that requirement x candidate is gap or not_assessable.

    Does NOT modify biographical_pattern or other evidence types.

    Args:
        verdict: Agent verdict to audit.
        candidate_data: All candidates with raw CV text.
        rubric_assessments: Stage C rubric assessment matrix.
        requirements: Confirmed JD requirement list.

    Returns:
        New AgentVerdict with invalid claims stripped, and warnings list.
    """
    warnings: list[str] = []
    kept_claims: list[Claim] = []

    for claim in verdict.claims:
        eb_type = claim.evidence_basis.type
        warning: str | None = None

        if eb_type == AgentEvidenceType.CV_RUBRIC:
            warning = _check_cv_rubric_claim(claim, candidate_data, rubric_assessments)
        elif eb_type == AgentEvidenceType.REQUIREMENT_GAP:
            warning = _check_requirement_gap_claim(claim, rubric_assessments, requirements)

        if warning is not None:
            warnings.append(warning)
            logger.warning(warning)
        else:
            kept_claims.append(claim)

    if len(kept_claims) == len(verdict.claims):
        return verdict, warnings

    updated = verdict.model_copy(update={"claims": kept_claims})
    return updated, warnings


# ---------------------------------------------------------------------------
# Check 6 (F05): Semantic Drift Detection
# ---------------------------------------------------------------------------


def _keyword_overlap_ratio(text: str, keywords: list[str]) -> float:
    """Compute the fraction of keywords that appear in the text.

    Case-insensitive, whole-word matching via word boundary split.
    Returns 1.0 if keywords is empty (no drift possible).
    """
    if not keywords:
        return 1.0  # No keywords to check — no drift possible.

    text_words = frozenset(re.findall(r"[a-z0-9]+", text.lower()))
    matched = sum(1 for kw in keywords if kw.lower() in text_words)
    return matched / len(keywords)


def _flag_keywords_for_claim(
    claim: Claim,
    flags: list[Flag],
) -> list[str]:
    """Return topic_keywords for the flag or requirement referenced in a claim."""
    eb = claim.evidence_basis

    if eb.type == AgentEvidenceType.SCORED_FLAG:
        for flag in flags:
            if flag.name == eb.reference and flag.candidate_name == claim.candidate_name:
                return flag.topic_keywords

    elif eb.type in (AgentEvidenceType.CV_RUBRIC, AgentEvidenceType.REQUIREMENT_GAP):
        # For CV-derived references: use topic_keywords from the corresponding CV flag.
        for flag in flags:
            if flag.requirement_id == eb.reference and flag.candidate_name == claim.candidate_name:
                return flag.topic_keywords

    return []


def check_semantic_drift(
    verdict: AgentVerdict,
    flags: list[Flag],
    drift_threshold: float = 0.2,
) -> list[str]:
    """Detect semantic drift between claim text and flag/requirement keywords (F05).

    Computes keyword overlap between the claim text and the topic_keywords of the
    flag or requirement the claim references. Overlap below drift_threshold triggers
    a SEMANTIC_DRIFT_WARNING.

    Does NOT strip claims — adds [DRIFT] warning markers only.

    Args:
        verdict: Agent verdict to audit.
        flags: All flags available to this agent (allowlist-filtered).
        drift_threshold: Minimum required keyword overlap ratio. Default 0.2 (20%).

    Returns:
        List of [DRIFT] warning strings (empty if all claims are on-topic).
    """
    warnings: list[str] = []

    for claim in verdict.claims:
        if claim.evidence_basis.type not in (
            AgentEvidenceType.SCORED_FLAG,
            AgentEvidenceType.CV_RUBRIC,
            AgentEvidenceType.REQUIREMENT_GAP,
        ):
            continue

        keywords = _flag_keywords_for_claim(claim, flags)
        if not keywords:
            continue

        ratio = _keyword_overlap_ratio(claim.text, keywords)
        if ratio < drift_threshold:
            warnings.append(
                f"[DRIFT] Semantic drift in '{verdict.agent_role}' claim "
                f"(candidate='{claim.candidate_name}', ref='{claim.evidence_basis.reference}'): "
                f"{ratio:.0%} keyword overlap (threshold {drift_threshold:.0%})"
            )

    return warnings


# ---------------------------------------------------------------------------
# Check 7 (F07): research_general Cap
# ---------------------------------------------------------------------------


def check_research_general_cap(
    verdict: AgentVerdict,
    cap: int = 2,
) -> list[str]:
    """Verify research_general evidence count does not exceed cap (F07).

    With CV-derived evidence now available, hitting the cap is a stronger
    signal than in v4.1 — it means the agent could not ground claims in data.

    Wraps the existing validate_research_general_cap helper from schemas.py.

    Args:
        verdict: Agent verdict to audit.
        cap: Maximum allowed research_general claims. Default 2.

    Returns:
        List of warning strings (empty if within cap).
    """
    raw_warnings = validate_research_general_cap(verdict, cap=cap)
    return [f"[CHECK7] {w}" for w in raw_warnings]


# ---------------------------------------------------------------------------
# Check 8 (F14): Downweight Ratio Warning
# ---------------------------------------------------------------------------


def check_downweight_ratio(
    verdict: AgentVerdict,
    agent_flags: list[Flag],
    threshold: float = 0.5,
) -> list[str]:
    """Warn if the agent downweights more than threshold fraction of in-mandate flags (F14).

    "Downweighted" means the agent received a flag but did not cite it in any claim.
    Applies to both personality (scored_flag) and CV-derived flags.

    The flag set is deduplicated by (name, candidate_name) before counting because
    the same flag name should not appear more than once per candidate — but defensive
    deduplication ensures the ratio is not inflated by duplicate flag entries.

    Args:
        verdict: Agent verdict to audit.
        agent_flags: Flags that were passed to this agent (allowlist-filtered).
        threshold: Maximum allowed uncited fraction. Default 0.5 (50%).

    Returns:
        List of warning strings (empty if within threshold).
    """
    if not agent_flags:
        return []

    # Deduplicate by (name, candidate_name)
    unique_flags: set[tuple[str, str]] = {(f.name, f.candidate_name) for f in agent_flags}
    available_count = len(unique_flags)

    # Collect all flag references cited in claims (scored_flag or cv-derived via requirement_id)
    cited_flag_names: set[str] = set()
    cited_req_ids: set[str] = set()

    for claim in verdict.claims:
        eb = claim.evidence_basis
        if eb.type == AgentEvidenceType.SCORED_FLAG:
            cited_flag_names.add(eb.reference)
        elif eb.type in (AgentEvidenceType.CV_RUBRIC, AgentEvidenceType.REQUIREMENT_GAP):
            cited_req_ids.add(eb.reference)

    # Count how many unique flags were cited (matched by flag name or via requirement_id)
    cited_count = 0
    for flag_name, cand_name in unique_flags:
        flag_obj = next(
            (f for f in agent_flags if f.name == flag_name and f.candidate_name == cand_name),
            None,
        )
        if flag_obj is None:
            continue

        req_id = flag_obj.requirement_id
        if flag_name in cited_flag_names or (req_id is not None and req_id in cited_req_ids):
            cited_count += 1

    uncited_fraction = (available_count - cited_count) / available_count

    if uncited_fraction > threshold:
        return [
            f"[CHECK8] Downweight ratio warning for '{verdict.agent_role}': "
            f"{cited_count}/{available_count} in-mandate flags cited "
            f"({uncited_fraction:.0%} uncited, threshold {threshold:.0%})"
        ]
    return []


# ---------------------------------------------------------------------------
# Re-export canonical flag vocabulary for use by the runner
# ---------------------------------------------------------------------------

ALL_FLAG_NAMES: frozenset[str] = _ALL_FLAG_NAMES
