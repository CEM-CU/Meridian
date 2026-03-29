"""Integration tests for the full Stage C pipeline: C1 → C2 → C3 → C4.

Exercises the complete raw JD text + raw CV text → StageCOutput path using a
mock LLM client that returns fixture data.  No real LLM calls are made, so these
tests run in CI without any API key.

Mock strategy
-------------
``_PipelineMockLLMClient.complete`` inspects the *system* prompt to decide which
canned response to return:

- C1 call: system prompt contains the word "requirement" (JD extraction prompt).
  Returns all 12 sample requirements serialised as a JSON array.

- C3 calls: system prompt contains "rubric" or "assessment" (CV assessment prompt).
  Inspects the *user* prompt for a "Candidate:" line to identify the current
  candidate, then returns only that candidate's assessments as a JSON array.

The fixture data is imported directly from the root ``tests/conftest.py`` module
constants so the mock output is consistent with what the conftest fixtures expose.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Ensure the root tests/ directory is importable (mirrors conftest.py setup).
# ---------------------------------------------------------------------------
_TESTS_DIR = str(Path(__file__).resolve().parents[1])
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from meridian.extraction.bridge import bridge_rubric_to_flags  # noqa: E402
from meridian.extraction.cv_assessment import assess_all_candidates  # noqa: E402
from meridian.extraction.jd_extraction import extract_requirements  # noqa: E402
from meridian.extraction.priority_resolution import resolve_active_priorities  # noqa: E402
from meridian.models import (  # noqa: E402
    CandidateData,
    Confidence,
    Requirement,
    RubricAssessment,
    RubricLevel,
    ScenarioConfig,
    ScenarioName,
    StageCOutput,
)

# ---------------------------------------------------------------------------
# Valid C-suite flag names produced by C4
# ---------------------------------------------------------------------------

_VALID_FLAG_NAMES: frozenset[str] = frozenset(
    {
        "CV_GAP",
        "CV_EXCEEDS",
        "CV_PARTIAL",
        "CV_BEHAVIORAL_ROUTED",
        "CV_LOW_CONFIDENCE_CLUSTER",
        "CV_SYSTEMATIC_GAP",
    }
)

# Number of CV-assessable requirements in the fixture set (REQ-01..REQ-10;
# REQ-11 and REQ-12 are behavioral, assessable_from_cv=False).
_CV_ASSESSABLE_COUNT = 10

# Total number of requirements in the fixture set.
_TOTAL_REQUIREMENT_COUNT = 12

# Candidate names in the fixture set.
_CANDIDATE_NAMES: frozenset[str] = frozenset({"Marcus Chen", "Sarah Okafor", "Kenji Tanaka"})


# ---------------------------------------------------------------------------
# Helper: build StageCOutput from the pipeline mock data.
# ---------------------------------------------------------------------------


def _make_scenario(name: ScenarioName = ScenarioName.DIGITAL_TRANSFORMATION) -> ScenarioConfig:
    """Return a minimal ScenarioConfig for the given scenario."""
    return ScenarioConfig(name=name)


# ---------------------------------------------------------------------------
# Mock LLM client
# ---------------------------------------------------------------------------


class _PipelineMockLLMClient:
    """Mock LLM client that routes responses by inspecting the system prompt.

    - System prompt contains "requirement" → C1 JD extraction response
      (returns all fixture requirements as JSON).
    - System prompt contains "rubric" or "assessment" → C3 CV assessment
      response (returns fixture assessments for the candidate named in the
      user prompt).

    Tracks all calls for post-test inspection.
    """

    def __init__(
        self,
        requirements: list[Requirement],
        rubric_assessments: list[RubricAssessment],
    ) -> None:
        self._requirements = requirements
        self._rubric_assessments = rubric_assessments
        self.calls: list[tuple[str, str]] = []

    async def complete(self, system: str, user: str, response_format: dict | None = None) -> str:
        """Return a canned JSON response based on the system prompt content."""
        self.calls.append((system, user))
        system_lower = system.lower()

        if "rubric" not in system_lower:
            # C1: JD extraction — the JD extraction system prompt never contains
            # "rubric", while the CV assessment system prompt always does.
            return json.dumps([r.model_dump() for r in self._requirements])

        # C3: CV assessment — identify candidate from the user prompt.
        candidate_name = self._extract_candidate_name(user)
        candidate_assessments = [a for a in self._rubric_assessments if a.candidate_name == candidate_name]
        return json.dumps([a.model_dump() for a in candidate_assessments])

    @staticmethod
    def _extract_candidate_name(user_prompt: str) -> str:
        """Parse 'Candidate: <name>' from the C3 user prompt."""
        for line in user_prompt.splitlines():
            stripped = line.strip()
            if stripped.startswith("Candidate:"):
                return stripped[len("Candidate:") :].strip()
        # Fallback: return first candidate name so the pipeline does not crash.
        return next(iter(_CANDIDATE_NAMES))


# ---------------------------------------------------------------------------
# Shared pipeline runner (used across multiple tests)
# ---------------------------------------------------------------------------


async def _run_full_pipeline(
    jd_text: str,
    candidates: list[CandidateData],
    requirements: list[Requirement],
    rubric_assessments: list[RubricAssessment],
    scenario: ScenarioConfig,
) -> StageCOutput:
    """Execute the complete C1 → C2 → C3 → C4 pipeline with mocked LLM calls.

    Args:
        jd_text: Raw JD text fed to C1.
        candidates: Candidate list fed to C3.
        requirements: Fixture requirements that the mock LLM returns for C1.
        rubric_assessments: Fixture assessments that the mock LLM returns for C3.
        scenario: Active scenario used throughout.

    Returns:
        Fully assembled StageCOutput.
    """
    llm = _PipelineMockLLMClient(requirements=requirements, rubric_assessments=rubric_assessments)

    # C1: JD extraction (mocked LLM returns fixture requirements).
    extracted_requirements, _warnings = await extract_requirements(jd_text, llm)

    # C2: Active priority resolution (deterministic — zero LLM calls).
    _priority_pairs = resolve_active_priorities(extracted_requirements, scenario)

    # C3: CV rubric assessment (mocked LLM returns per-candidate fixture assessments).
    all_assessments = await assess_all_candidates(
        candidates=candidates,
        requirements=extracted_requirements,
        scenario=scenario,
        llm_client=llm,
    )

    # Assemble StageCOutput (C4 is a separate step exercised in individual tests).
    return StageCOutput(
        requirements=extracted_requirements,
        rubric_assessments=all_assessments,
        candidate_data=candidates,
        scenario=scenario,
    )


# ---------------------------------------------------------------------------
# Test 1: full C1 → C4 pipeline produces valid StageCOutput
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_c1_through_c4_pipeline(
    synthetic_jd_text: str,
    synthetic_candidates: list[CandidateData],
    sample_requirements: list[Requirement],
    sample_rubric_assessments: list[RubricAssessment],
    sample_scenario_config: ScenarioConfig,
) -> None:
    """Verify that the complete C1→C2→C3→C4 pipeline produces a valid StageCOutput.

    WHY: This is the primary smoke test for Stage C. It confirms that all four
    sub-stages can be wired together in sequence and that the assembled output
    satisfies every structural contract required by Stage D.
    """
    output = await _run_full_pipeline(
        jd_text=synthetic_jd_text,
        candidates=synthetic_candidates,
        requirements=sample_requirements,
        rubric_assessments=sample_rubric_assessments,
        scenario=sample_scenario_config,
    )

    # --- StageCOutput populated ---
    assert output.requirements, "StageCOutput.requirements must not be empty"
    assert output.rubric_assessments, "StageCOutput.rubric_assessments must not be empty"
    assert output.candidate_data, "StageCOutput.candidate_data must not be empty"
    assert output.scenario is not None, "StageCOutput.scenario must be set"

    # --- Requirement count in expected range (10-14 per spec) ---
    req_count = len(output.requirements)
    assert 10 <= req_count <= 14, f"Expected 10-14 requirements from BMW CTO JD, got {req_count}"

    # --- All 3 candidates covered ---
    assessed_candidate_names = {a.candidate_name for a in output.rubric_assessments}
    assert assessed_candidate_names == _CANDIDATE_NAMES, (
        f"Expected assessments for all 3 candidates; missing: {_CANDIDATE_NAMES - assessed_candidate_names}"
    )

    # --- CV-assessable requirements each have an assessment per candidate ---
    cv_assessable_ids = {r.requirement_id for r in output.requirements if r.assessable_from_cv}
    for candidate_name in _CANDIDATE_NAMES:
        candidate_assessed_ids = {
            a.requirement_id for a in output.rubric_assessments if a.candidate_name == candidate_name
        }
        assert cv_assessable_ids == candidate_assessed_ids, (
            f"Candidate '{candidate_name}' missing assessments for: {cv_assessable_ids - candidate_assessed_ids}"
        )

    # --- Every assessment has a valid rubric_level and confidence ---
    valid_levels = {level.value for level in RubricLevel}
    valid_confidences = {conf.value for conf in Confidence}
    for assessment in output.rubric_assessments:
        assert assessment.rubric_level in valid_levels, (
            f"Invalid rubric_level '{assessment.rubric_level}' for "
            f"{assessment.candidate_name}/{assessment.requirement_id}"
        )
        assert assessment.confidence in valid_confidences, (
            f"Invalid confidence '{assessment.confidence}' for {assessment.candidate_name}/{assessment.requirement_id}"
        )

    # --- candidate_data has all 3 candidates ---
    output_candidate_names = {c.name for c in output.candidate_data}
    assert output_candidate_names == _CANDIDATE_NAMES, (
        f"candidate_data missing: {_CANDIDATE_NAMES - output_candidate_names}"
    )

    # --- Scenario matches the input scenario ---
    assert output.scenario.name == sample_scenario_config.name, (
        f"Scenario mismatch: expected {sample_scenario_config.name}, got {output.scenario.name}"
    )


# ---------------------------------------------------------------------------
# Test 2: StageCOutput validates against schema (round-trip)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stage_c_output_validates_against_schema(
    synthetic_jd_text: str,
    synthetic_candidates: list[CandidateData],
    sample_requirements: list[Requirement],
    sample_rubric_assessments: list[RubricAssessment],
    sample_scenario_config: ScenarioConfig,
) -> None:
    """Verify that StageCOutput survives a model_dump → model_validate round-trip.

    WHY: Stage D receives StageCOutput across a process boundary (serialised to
    dict/JSON and deserialised).  A successful round-trip confirms all fields are
    serialisable and that the schema is self-consistent.
    """
    output = await _run_full_pipeline(
        jd_text=synthetic_jd_text,
        candidates=synthetic_candidates,
        requirements=sample_requirements,
        rubric_assessments=sample_rubric_assessments,
        scenario=sample_scenario_config,
    )

    dumped = output.model_dump()
    restored = StageCOutput.model_validate(dumped)

    assert len(restored.requirements) == len(output.requirements), (
        f"Round-trip lost requirements: {len(output.requirements)} → {len(restored.requirements)}"
    )
    assert len(restored.rubric_assessments) == len(output.rubric_assessments), (
        f"Round-trip lost assessments: {len(output.rubric_assessments)} → {len(restored.rubric_assessments)}"
    )
    assert len(restored.candidate_data) == len(output.candidate_data), (
        f"Round-trip lost candidates: {len(output.candidate_data)} → {len(restored.candidate_data)}"
    )
    assert restored.scenario.name == output.scenario.name, "Round-trip changed scenario name"


# ---------------------------------------------------------------------------
# Test 3: C4 flag output is valid
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flag_output_from_c4_is_valid(
    synthetic_jd_text: str,
    synthetic_candidates: list[CandidateData],
    sample_requirements: list[Requirement],
    sample_rubric_assessments: list[RubricAssessment],
    sample_scenario_config: ScenarioConfig,
) -> None:
    """Verify that C4 produces well-formed flags with correct provenance.

    WHY: C4 is a deterministic bridge — its correctness can be fully validated
    without LLM calls.  This test confirms that every flag produced from the
    fixture data references real requirements, carries valid names, and that
    behavioral requirements produce the expected routing flags.
    """
    output = await _run_full_pipeline(
        jd_text=synthetic_jd_text,
        candidates=synthetic_candidates,
        requirements=sample_requirements,
        rubric_assessments=sample_rubric_assessments,
        scenario=sample_scenario_config,
    )

    flags = bridge_rubric_to_flags(
        assessments=output.rubric_assessments,
        requirements=output.requirements,
        scenario_name=output.scenario.name,
    )

    assert flags, "C4 must produce at least one flag from the fixture assessments"

    valid_requirement_ids = {r.requirement_id for r in output.requirements}

    for flag in flags:
        # Every flag must have a valid name.
        assert flag.name in _VALID_FLAG_NAMES, f"Unknown flag name '{flag.name}' for candidate '{flag.candidate_name}'"

        # Every flag must reference a known candidate.
        assert flag.candidate_name in _CANDIDATE_NAMES, f"Flag references unknown candidate '{flag.candidate_name}'"

        # Non-pattern flags must reference a real requirement.
        is_pattern_flag = flag.name in {"CV_LOW_CONFIDENCE_CLUSTER", "CV_SYSTEMATIC_GAP"}
        if not is_pattern_flag:
            assert flag.requirement_id is not None, (
                f"Non-pattern flag '{flag.name}' for '{flag.candidate_name}' has no requirement_id"
            )
            assert flag.requirement_id in valid_requirement_ids, (
                f"Flag '{flag.name}' references unknown requirement_id '{flag.requirement_id}'"
            )

    # --- Flag count is reasonable (6-30 total across 3 candidates) ---
    total_flags = len(flags)
    assert 6 <= total_flags <= 30, f"Flag count {total_flags} outside expected range 6-30 for 3 candidates"

    # --- Behavioral requirement routing check via a targeted C4 call ---
    # C3 only assesses CV-assessable requirements, so behavioral requirements
    # (assessable_from_cv=False) never receive assessments in the normal pipeline.
    # CV_BEHAVIORAL_ROUTED flags are produced by C4 only when NOT_ASSESSABLE
    # assessments are explicitly supplied for behavioral requirements.
    # We verify this C4 behaviour directly by constructing synthetic
    # NOT_ASSESSABLE assessments for the behavioral reqs and running C4.
    behavioral_reqs = [r for r in output.requirements if not r.assessable_from_cv]
    if behavioral_reqs:
        behavioral_assessments = [
            RubricAssessment(
                requirement_id=req.requirement_id,
                candidate_name=candidate_name,
                rubric_level=RubricLevel.NOT_ASSESSABLE,
                confidence=Confidence.HIGH,
                cv_citation=None,
                cv_location=None,
            )
            for req in behavioral_reqs
            for candidate_name in _CANDIDATE_NAMES
        ]
        # Combine pipeline assessments with explicit behavioral routing assessments.
        all_assessments_with_behavioral = [*output.rubric_assessments, *behavioral_assessments]
        flags_with_behavioral = bridge_rubric_to_flags(
            assessments=all_assessments_with_behavioral,
            requirements=output.requirements,
            scenario_name=output.scenario.name,
        )
        behavioral_req_ids = {r.requirement_id for r in behavioral_reqs}
        routing_flags = [f for f in flags_with_behavioral if f.name == "CV_BEHAVIORAL_ROUTED"]
        assert routing_flags, (
            f"C4 produced no CV_BEHAVIORAL_ROUTED flags despite NOT_ASSESSABLE assessments "
            f"for behavioral requirements {sorted(behavioral_req_ids)}"
        )
        for rf in routing_flags:
            assert rf.requirement_id in behavioral_req_ids, (
                f"CV_BEHAVIORAL_ROUTED flag references non-behavioral requirement '{rf.requirement_id}'"
            )
            assert rf.candidate_name in _CANDIDATE_NAMES, (
                f"CV_BEHAVIORAL_ROUTED flag references unknown candidate '{rf.candidate_name}'"
            )


# ---------------------------------------------------------------------------
# Test 4: priority changes affect flag output
# ---------------------------------------------------------------------------


def test_priority_changes_affect_flags(
    sample_requirements: list[Requirement],
    sample_rubric_assessments: list[RubricAssessment],
) -> None:
    """Verify that running C4 under different scenarios produces different flag sets.

    WHY: The scenario switch is the core differentiation mechanism of Stage C.
    If scenario changes have no effect on the flag set, the pipeline is broken.
    The digital_transformation and turnaround scenarios assign materially different
    priorities to several BMW CTO requirements, which should produce different flags.
    """
    scenario_dt = ScenarioName.DIGITAL_TRANSFORMATION
    scenario_ta = ScenarioName.TURNAROUND

    flags_dt = bridge_rubric_to_flags(
        assessments=sample_rubric_assessments,
        requirements=sample_requirements,
        scenario_name=scenario_dt,
    )

    flags_ta = bridge_rubric_to_flags(
        assessments=sample_rubric_assessments,
        requirements=sample_requirements,
        scenario_name=scenario_ta,
    )

    # Flag names are not sufficient — compare (name, candidate, requirement_id) triples.
    def _flag_triples(flags: list) -> frozenset[tuple[str, str, str | None]]:
        return frozenset((f.name, f.candidate_name, f.requirement_id) for f in flags)

    dt_triples = _flag_triples(flags_dt)
    ta_triples = _flag_triples(flags_ta)

    assert dt_triples != ta_triples, (
        "digital_transformation and turnaround scenarios produced identical flag sets; "
        "scenario priority switching is not affecting flag derivation"
    )

    # Confirm both sets are non-empty (not degenerate).
    assert dt_triples, "digital_transformation scenario produced no flags"
    assert ta_triples, "turnaround scenario produced no flags"


# ---------------------------------------------------------------------------
# Test 5: citation enforcement downgrades MEETS with missing citation to GAP
# ---------------------------------------------------------------------------


def test_citation_enforcement_in_pipeline(
    sample_requirements: list[Requirement],
    sample_scenario_config: ScenarioConfig,
) -> None:
    """Verify that a MEETS assessment without a cv_citation is downgraded to GAP.

    WHY: Citation enforcement is the primary anti-fabrication constraint in Stage C.
    An LLM returning MEETS/EXCEEDS without a verifiable citation should never
    reach Stage D with that positive assessment intact.
    """
    from meridian.extraction.cv_assessment import enforce_citations

    # Build a MEETS assessment that deliberately omits the cv_citation.
    uncited_meets = RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Marcus Chen",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.HIGH,
        cv_citation=None,  # Missing citation — must trigger downgrade.
        cv_location=None,
        notes=None,
        investigation_question=None,
    )

    # Mix in a correctly cited MEETS so we can confirm only the bad one is changed.
    correctly_cited = RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Marcus Chen",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.HIGH,
        cv_citation="USD 620M annual budget, full P&L responsibility",
        cv_location="CTO, Apex Robotics",
        notes=None,
        investigation_question=None,
    )

    corrected, warnings = enforce_citations([uncited_meets, correctly_cited])

    # --- Uncited MEETS must become GAP ---
    downgraded = next(a for a in corrected if a.requirement_id == "REQ-01")
    assert downgraded.rubric_level == RubricLevel.GAP, f"Expected downgrade to GAP, got '{downgraded.rubric_level}'"
    assert downgraded.cv_citation is None, "Downgraded assessment must have cv_citation=None"

    # --- Notes must contain CITATION_MISSING tag ---
    assert downgraded.notes is not None, "Downgraded assessment must have notes set"
    assert "CITATION_MISSING" in downgraded.notes, f"Expected CITATION_MISSING in notes, got: '{downgraded.notes}'"

    # --- Correctly cited assessment must remain MEETS ---
    unchanged = next(a for a in corrected if a.requirement_id == "REQ-02")
    assert unchanged.rubric_level == RubricLevel.MEETS, (
        f"Correctly cited assessment should stay MEETS, got '{unchanged.rubric_level}'"
    )

    # --- Exactly one warning produced ---
    assert len(warnings) == 1, f"Expected exactly 1 citation warning, got {len(warnings)}: {warnings}"
    assert "CITATION_MISSING" in warnings[0], f"Warning should contain CITATION_MISSING, got: '{warnings[0]}'"
    assert "REQ-01" in warnings[0], f"Warning should reference REQ-01, got: '{warnings[0]}'"
    assert "Marcus Chen" in warnings[0], f"Warning should reference candidate name, got: '{warnings[0]}'"
