"""Integration test: full C1 → C2 → C3 → C4 pipeline.

Uses synthetic fixtures with mocked LLM responses. Validates the StageCOutput
contract and CV flag output end-to-end.
"""

from __future__ import annotations

import json

import pytest
from _helpers import MockLLMClient, make_assessment_dict

from meridian.extraction.pipeline import run_stage_c
from meridian.models import (
    CandidateData,
    EvidenceType,
    FlagCategory,
    ScenarioConfig,
    ScenarioName,
    Valence,
)
from meridian.models.pipeline import StageCOutput

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_JD_REQUIREMENTS = [
    {
        "requirement_id": "REQ-01",
        "text": "12+ years progressive technology leadership",
        "source_quote": "12+ years of progressive technology leadership",
        "assessable_from_cv": True,
        "scenario_priority": {
            "digital_transformation": "high",
            "post_acquisition": "high",
            "turnaround": "medium",
            "stabilization": "medium",
            "growth": "high",
        },
    },
    {
        "requirement_id": "REQ-02",
        "text": "P&L accountability of USD 500M+",
        "source_quote": "managing a P&L of USD 500M+",
        "assessable_from_cv": True,
        "scenario_priority": {
            "digital_transformation": "high",
            "post_acquisition": "high",
            "turnaround": "high",
            "stabilization": "high",
            "growth": "medium",
        },
    },
    {
        "requirement_id": "REQ-03",
        "text": "Ability to navigate complex stakeholder landscapes",
        "source_quote": "navigate complex stakeholder landscapes",
        "assessable_from_cv": False,
        "scenario_priority": {
            "digital_transformation": "high",
            "post_acquisition": "high",
            "turnaround": "high",
            "stabilization": "high",
            "growth": "medium",
        },
    },
]


def _make_c1_response() -> str:
    """Mock LLM response for C1 JD extraction."""
    return json.dumps(_JD_REQUIREMENTS)


def _make_c3_response(candidate_name: str) -> str:
    """Mock LLM response for C3 CV assessment (CV-assessable reqs only)."""
    assessments = [
        make_assessment_dict(
            "REQ-01",
            candidate_name,
            "exceeds",
            "high",
            "15 years as CTO across multiple firms",
            "Career summary",
        ),
        make_assessment_dict(
            "REQ-02",
            candidate_name,
            "gap",
            "high",
            None,
            None,
            None,
            "What was the full P&L scope at previous role?",
        ),
    ]
    return json.dumps(assessments)


_CANDIDATES = [
    CandidateData(name="Alice", cv_text="Alice is a 15-year CTO veteran with deep tech leadership."),
    CandidateData(name="Bob", cv_text="Bob managed small teams at a startup for 5 years."),
]

_SCENARIO = ScenarioConfig(name=ScenarioName.DIGITAL_TRANSFORMATION)


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestStageCStageCPipeline:
    """Full C1→C2→C3→C4 integration tests."""

    @pytest.mark.asyncio
    async def test_pipeline_produces_valid_stage_c_output(self) -> None:
        """Full pipeline returns a valid StageCOutput with correct structure."""
        # C1 response + C3 responses (one per candidate)
        client = MockLLMClient([
            _make_c1_response(),
            _make_c3_response("Alice"),
            _make_c3_response("Bob"),
        ])

        output, _cv_flags, _warnings = await run_stage_c(
            jd_text="CTO position requiring 12+ years leadership and P&L accountability.",
            candidates=_CANDIDATES,
            scenario=_SCENARIO,
            llm_client=client,
        )

        # Validate StageCOutput structure
        assert isinstance(output, StageCOutput)
        assert len(output.requirements) == 3
        assert len(output.candidate_data) == 2
        assert output.scenario.name == ScenarioName.DIGITAL_TRANSFORMATION

    @pytest.mark.asyncio
    async def test_rubric_assessments_cover_all_cv_assessable_pairs(self) -> None:
        """Every (candidate x cv_assessable_requirement) pair has an assessment."""
        client = MockLLMClient([
            _make_c1_response(),
            _make_c3_response("Alice"),
            _make_c3_response("Bob"),
        ])

        output, _, _ = await run_stage_c(
            jd_text="JD text",
            candidates=_CANDIDATES,
            scenario=_SCENARIO,
            llm_client=client,
        )

        cv_assessable = [r for r in output.requirements if r.assessable_from_cv]
        expected_count = len(cv_assessable) * len(_CANDIDATES)
        assert len(output.rubric_assessments) == expected_count

        # Every cv_assessable req x candidate combination is present
        pairs = {(a.requirement_id, a.candidate_name) for a in output.rubric_assessments}
        for req in cv_assessable:
            for cand in _CANDIDATES:
                assert (req.requirement_id, cand.name) in pairs

    @pytest.mark.asyncio
    async def test_behavioral_requirements_excluded_from_rubric(self) -> None:
        """Behavioral requirements (assessable_from_cv=False) have no rubric assessments."""
        client = MockLLMClient([
            _make_c1_response(),
            _make_c3_response("Alice"),
            _make_c3_response("Bob"),
        ])

        output, _, _ = await run_stage_c(
            jd_text="JD text",
            candidates=_CANDIDATES,
            scenario=_SCENARIO,
            llm_client=client,
        )

        behavioral_ids = {r.requirement_id for r in output.requirements if not r.assessable_from_cv}
        assessed_ids = {a.requirement_id for a in output.rubric_assessments}
        assert behavioral_ids.isdisjoint(assessed_ids)

    @pytest.mark.asyncio
    async def test_cv_flags_produced_with_valid_structure(self) -> None:
        """Bridge produces CV flags with correct evidence types and provenance."""
        client = MockLLMClient([
            _make_c1_response(),
            _make_c3_response("Alice"),
            _make_c3_response("Bob"),
        ])

        _, cv_flags, _ = await run_stage_c(
            jd_text="JD text",
            candidates=_CANDIDATES,
            scenario=_SCENARIO,
            llm_client=client,
        )

        assert len(cv_flags) > 0
        valid_evidence_types = {
            EvidenceType.CV_RUBRIC,
            EvidenceType.REQUIREMENT_GAP,
            EvidenceType.CV_PATTERN,
            EvidenceType.ROUTING,
        }
        for flag in cv_flags:
            assert flag.evidence_type in valid_evidence_types
            assert flag.candidate_name in {"Alice", "Bob"}

    @pytest.mark.asyncio
    async def test_gap_on_high_priority_produces_cv_gap_flag(self) -> None:
        """REQ-02 is GAP + high priority under digital_transformation → CV_GAP flag."""
        client = MockLLMClient([
            _make_c1_response(),
            _make_c3_response("Alice"),
            _make_c3_response("Bob"),
        ])

        _, cv_flags, _ = await run_stage_c(
            jd_text="JD text",
            candidates=_CANDIDATES,
            scenario=_SCENARIO,
            llm_client=client,
        )

        gap_flags = [f for f in cv_flags if f.name == "CV_GAP"]
        assert len(gap_flags) >= 2  # one per candidate for REQ-02
        for flag in gap_flags:
            assert flag.requirement_id == "REQ-02"
            assert flag.category == FlagCategory.EXPERIENCE_GAP
            assert flag.valence == Valence.NEGATIVE

    @pytest.mark.asyncio
    async def test_exceeds_on_high_priority_produces_cv_exceeds_flag(self) -> None:
        """REQ-01 is EXCEEDS + high priority under digital_transformation → CV_EXCEEDS flag."""
        client = MockLLMClient([
            _make_c1_response(),
            _make_c3_response("Alice"),
            _make_c3_response("Bob"),
        ])

        _, cv_flags, _ = await run_stage_c(
            jd_text="JD text",
            candidates=_CANDIDATES,
            scenario=_SCENARIO,
            llm_client=client,
        )

        exceeds_flags = [f for f in cv_flags if f.name == "CV_EXCEEDS"]
        assert len(exceeds_flags) >= 2  # one per candidate for REQ-01
        for flag in exceeds_flags:
            assert flag.requirement_id == "REQ-01"
            assert flag.category == FlagCategory.EXPERIENCE_STRENGTH
            assert flag.valence == Valence.POSITIVE

    @pytest.mark.asyncio
    async def test_llm_call_count(self) -> None:
        """Pipeline makes exactly 1 C1 call + N C3 calls (one per candidate)."""
        client = MockLLMClient([
            _make_c1_response(),
            _make_c3_response("Alice"),
            _make_c3_response("Bob"),
        ])

        await run_stage_c(
            jd_text="JD text",
            candidates=_CANDIDATES,
            scenario=_SCENARIO,
            llm_client=client,
        )

        assert client.call_count == 3  # 1 C1 + 2 C3

    @pytest.mark.asyncio
    async def test_stage_c_output_validates_as_pydantic(self) -> None:
        """StageCOutput round-trips through Pydantic serialization."""
        client = MockLLMClient([
            _make_c1_response(),
            _make_c3_response("Alice"),
            _make_c3_response("Bob"),
        ])

        output, _, _ = await run_stage_c(
            jd_text="JD text",
            candidates=_CANDIDATES,
            scenario=_SCENARIO,
            llm_client=client,
        )

        # Round-trip through JSON
        json_str = output.model_dump_json()
        restored = StageCOutput.model_validate_json(json_str)
        assert len(restored.requirements) == len(output.requirements)
        assert len(restored.rubric_assessments) == len(output.rubric_assessments)
