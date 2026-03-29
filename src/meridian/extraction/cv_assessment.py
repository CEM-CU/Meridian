"""C3: CV rubric assessment pipeline.

Orchestrates parallel LLM calls (one per candidate) to assess all CV-assessable
requirements against each candidate's CV. Applies deterministic post-processing:
citation enforcement (missing citations → GAP downgrade) and requirement drop
detection (missing requirements from batch → targeted follow-up call).

No mutable state — every function takes typed inputs and returns typed outputs.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from meridian.models import (
    CandidateData,
    Priority,
    Requirement,
    RubricAssessment,
    RubricLevel,
    ScenarioConfig,
)

if TYPE_CHECKING:
    from meridian.extraction.protocols import LLMClient

from meridian.extraction.prompts.cv_assessment import build_cv_assessment_prompt
from meridian.extraction.text_utils import strip_markdown_fences

logger = logging.getLogger(__name__)

# Levels that REQUIRE a cv_citation; omitting one triggers a downgrade.
_CITATION_REQUIRED_LEVELS: frozenset[RubricLevel] = frozenset(
    {RubricLevel.EXCEEDS, RubricLevel.MEETS, RubricLevel.PARTIAL}
)

# Warning tag appended to notes on citation-based downgrades.
_CITATION_MISSING_TAG: str = "CITATION_MISSING"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_assessment_response(
    raw_json: str,
    candidate_name: str,
    requirement_ids: list[str],
) -> list[RubricAssessment]:
    """Parse LLM response into a RubricAssessment list.

    Strips markdown fences if present, validates each item against the
    RubricAssessment schema, and injects `candidate_name` if missing.

    Args:
        raw_json: Raw string from the LLM complete() call.
        candidate_name: Name of the candidate being assessed.
        requirement_ids: Expected requirement IDs (used only for caller reference;
            validation of completeness is done separately in detect_and_fill_drops).

    Returns:
        List of validated RubricAssessment objects.

    Raises:
        ValueError: If the JSON is invalid or any item fails schema validation.
    """
    cleaned = strip_markdown_fences(raw_json)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in CV assessment response: {exc}") from exc

    # Handle structured output wrapper: {"assessments": [...]}
    if isinstance(parsed, dict) and "assessments" in parsed:
        parsed = parsed["assessments"]

    if not isinstance(parsed, list):
        raise ValueError(f"Expected JSON array (or {{assessments: [...]}}), got {type(parsed).__name__}")

    assessments: list[RubricAssessment] = []
    for idx, item in enumerate(parsed):
        if not isinstance(item, dict):
            raise ValueError(f"Assessment at index {idx} is not a dict: {type(item).__name__}")

        # Inject candidate_name if LLM omitted it (common when batching).
        if "candidate_name" not in item or not item["candidate_name"]:
            item = {**item, "candidate_name": candidate_name}

        # Default null confidence to "high" — some models omit confidence for gap/not_assessable.
        if item.get("confidence") is None:
            item = {**item, "confidence": "high"}

        try:
            assessments.append(RubricAssessment.model_validate(item))
        except Exception as exc:
            raise ValueError(
                f"Assessment at index {idx} (req={item.get('requirement_id', '?')}) failed validation: {exc}"
            ) from exc

    return assessments


# ---------------------------------------------------------------------------
# Citation enforcement
# ---------------------------------------------------------------------------


def enforce_citations(
    assessments: list[RubricAssessment],
) -> tuple[list[RubricAssessment], list[str]]:
    """Downgrade EXCEEDS/MEETS/PARTIAL to GAP if cv_citation is missing.

    This is the primary anti-fabrication constraint in Stage C. An LLM that
    cannot produce a specific citation for a positive assessment is likely
    hallucinating evidence.

    Args:
        assessments: List of RubricAssessment objects to check.

    Returns:
        Tuple of (corrected_assessments, warnings). Returns a new list — does
        not mutate the input.
    """
    corrected: list[RubricAssessment] = []
    warnings: list[str] = []

    for assessment in assessments:
        if assessment.rubric_level in _CITATION_REQUIRED_LEVELS and not assessment.cv_citation:
            original_level = assessment.rubric_level.value
            warning = (
                f"{_CITATION_MISSING_TAG}: {assessment.candidate_name} / "
                f"{assessment.requirement_id} — {original_level} downgraded to gap "
                f"(no cv_citation provided)"
            )
            warnings.append(warning)
            # Build downgraded assessment immutably
            downgraded_notes = assessment.notes or ""
            if downgraded_notes:
                downgraded_notes = f"{downgraded_notes} [{_CITATION_MISSING_TAG}: originally {original_level}]"
            else:
                downgraded_notes = f"[{_CITATION_MISSING_TAG}: originally {original_level}]"
            corrected.append(
                assessment.model_copy(
                    update={
                        "rubric_level": RubricLevel.GAP,
                        "cv_citation": None,
                        "cv_location": None,
                        "notes": downgraded_notes,
                    }
                )
            )
        else:
            corrected.append(assessment)

    return corrected, warnings


# ---------------------------------------------------------------------------
# Drop detection + remediation
# ---------------------------------------------------------------------------


async def detect_and_fill_drops(
    assessments: list[RubricAssessment],
    candidate_name: str,
    cv_text: str,
    missing_requirement_ids: list[str],
    requirements: list[Requirement],
    priority_order: list[tuple[Requirement, Priority]],
    llm_client: LLMClient,
) -> list[RubricAssessment]:
    """Re-run LLM for any requirements dropped from the batch response.

    The batched call drops 1-2 requirements in ~5-10% of runs. This function
    fires a targeted follow-up call covering only the missing IDs and merges
    the results into the original list.

    Args:
        assessments: Existing assessments from the primary call.
        candidate_name: Name of the candidate being assessed.
        cv_text: Raw CV text (will be sanitized in prompt builder).
        missing_requirement_ids: IDs that were absent from the primary response.
        requirements: Full requirement list (for building the follow-up prompt).
        priority_order: Full priority ordering (filtered to missing reqs only).
        llm_client: Async LLM client.

    Returns:
        Extended list of assessments including the remediated entries.
        Returns the original list unchanged if missing_requirement_ids is empty.
    """
    if not missing_requirement_ids:
        return assessments

    missing_id_set = set(missing_requirement_ids)

    # Filter requirements and priority_order to only the missing IDs.
    missing_reqs = [r for r in requirements if r.requirement_id in missing_id_set]
    missing_priority_order = [(req, pri) for req, pri in priority_order if req.requirement_id in missing_id_set]

    logger.info(
        "Drop detection: %d requirements missing for candidate=%s; firing follow-up call",
        len(missing_requirement_ids),
        candidate_name,
    )

    system_prompt, user_prompt = build_cv_assessment_prompt(
        requirements=missing_reqs,
        candidate_name=candidate_name,
        cv_text=cv_text,
        priority_order=missing_priority_order,
    )

    raw_response = await llm_client.complete(system=system_prompt, user=user_prompt)
    missing_req_ids = [r.requirement_id for r in missing_reqs]
    remediated = parse_assessment_response(raw_response, candidate_name, missing_req_ids)
    remediated_checked, citation_warnings = enforce_citations(remediated)

    for w in citation_warnings:
        logger.warning("Citation enforcement (drop-fill): %s", w)

    return [*assessments, *remediated_checked]


# ---------------------------------------------------------------------------
# Single-candidate assessment
# ---------------------------------------------------------------------------


async def assess_candidate(
    candidate_name: str,
    cv_text: str,
    requirements: list[Requirement],
    priority_order: list[tuple[Requirement, Priority]],
    llm_client: LLMClient,
    response_format: dict | None = None,
) -> list[RubricAssessment]:
    """Assess one candidate against all CV-assessable requirements.

    Single LLM call. Applies citation enforcement and drop detection after
    the primary response. May fire a follow-up call if requirements were dropped.

    Args:
        candidate_name: Exact candidate name — embedded in each RubricAssessment.
        cv_text: Raw CV text. Sanitized in the prompt builder (F18).
        requirements: CV-assessable requirements only (already filtered).
        priority_order: Same requirements ordered by priority (high first).
        llm_client: Async LLM client satisfying the LLMClient protocol.

    Returns:
        List of RubricAssessment objects — one per input requirement.
    """
    system_prompt, user_prompt = build_cv_assessment_prompt(
        requirements=requirements,
        candidate_name=candidate_name,
        cv_text=cv_text,
        priority_order=priority_order,
    )

    raw_response = await llm_client.complete(
        system=system_prompt, user=user_prompt, response_format=response_format
    )
    logger.info(
        "LLM response received for CV assessment: candidate=%s, response_chars=%d",
        candidate_name,
        len(raw_response),
    )

    requirement_ids = [r.requirement_id for r in requirements]
    valid_ids = set(requirement_ids)
    assessments = parse_assessment_response(raw_response, candidate_name, requirement_ids)
    assessments, citation_warnings = enforce_citations(assessments)

    for w in citation_warnings:
        logger.warning("Citation enforcement: %s", w)

    # Strip assessments for requirement IDs not in the input list (LLM hallucination).
    pre_filter_count = len(assessments)
    assessments = [a for a in assessments if a.requirement_id in valid_ids]
    if len(assessments) < pre_filter_count:
        logger.warning(
            "Filtered %d hallucinated requirement ID(s) for candidate=%s",
            pre_filter_count - len(assessments),
            candidate_name,
        )

    # Drop detection: check all required IDs are present in the response.
    assessed_ids = {a.requirement_id for a in assessments}
    missing_ids = [rid for rid in requirement_ids if rid not in assessed_ids]

    if missing_ids:
        logger.warning(
            "Drop detection: candidate=%s missing %d requirement(s): %s",
            candidate_name,
            len(missing_ids),
            missing_ids,
        )
        assessments = await detect_and_fill_drops(
            assessments=assessments,
            candidate_name=candidate_name,
            cv_text=cv_text,
            missing_requirement_ids=missing_ids,
            requirements=requirements,
            priority_order=priority_order,
            llm_client=llm_client,
        )

    logger.info(
        "CV assessment complete: candidate=%s, assessment_count=%d",
        candidate_name,
        len(assessments),
    )
    return assessments


# ---------------------------------------------------------------------------
# Multi-candidate orchestration
# ---------------------------------------------------------------------------


def _build_priority_order(
    requirements: list[Requirement],
    scenario: ScenarioConfig,
) -> list[tuple[Requirement, Priority]]:
    """Resolve active priorities and order requirements high-first.

    Args:
        requirements: All requirements (CV-assessable only).
        scenario: Active scenario config providing the scenario name.

    Returns:
        List of (Requirement, Priority) tuples sorted high → medium → low.
    """
    priority_rank: dict[Priority, int] = {
        Priority.HIGH: 0,
        Priority.MEDIUM: 1,
        Priority.LOW: 2,
    }
    pairs: list[tuple[Requirement, Priority]] = []
    for req in requirements:
        active_priority = req.scenario_priority.for_scenario(scenario.name.value)
        pairs.append((req, active_priority))

    return sorted(pairs, key=lambda pair: priority_rank[pair[1]])


async def assess_all_candidates(
    candidates: list[CandidateData],
    requirements: list[Requirement],
    scenario: ScenarioConfig,
    llm_client: LLMClient,
    response_format: dict | None = None,
) -> list[RubricAssessment]:
    """Assess all candidates in parallel (asyncio.gather).

    Filters to CV-assessable requirements only. Orders requirements by priority
    (high first) for the prompt. Launches one LLM call per candidate concurrently.
    Returns a flat list of all assessments across all candidates.

    Args:
        candidates: All CandidateData objects to evaluate.
        requirements: Full requirement list from C1 (may include behavioral reqs).
        scenario: Active ScenarioConfig — used to resolve per-requirement priority.
        llm_client: Async LLM client.
        response_format: Optional structured output schema for OpenAI-compatible models.

    Returns:
        Flat list of RubricAssessment covering every (candidate x cv_assessable_req) pair.
    """
    cv_assessable = [r for r in requirements if r.assessable_from_cv]

    if not cv_assessable:
        logger.warning("assess_all_candidates: no CV-assessable requirements found; returning empty list")
        return []

    priority_order = _build_priority_order(cv_assessable, scenario)

    logger.info(
        "Launching parallel CV assessment: candidates=%d, cv_assessable_requirements=%d",
        len(candidates),
        len(cv_assessable),
    )

    tasks = [
        assess_candidate(
            candidate_name=candidate.name,
            cv_text=candidate.cv_text,
            requirements=cv_assessable,
            priority_order=priority_order,
            llm_client=llm_client,
            response_format=response_format,
        )
        for candidate in candidates
    ]

    results: list[list[RubricAssessment]] = await asyncio.gather(*tasks)

    flat: list[RubricAssessment] = [assessment for candidate_results in results for assessment in candidate_results]
    logger.info(
        "Parallel CV assessment complete: total_assessments=%d",
        len(flat),
    )
    return flat
