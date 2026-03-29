"""Shared fixtures and helper builders for pipeline stream tests (A4).

This module contains all fixture-building functions, mock factories, and
helper utilities used by test_pipeline_stream.py. Separated to keep the
test file under 800 lines.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from meridian.api.sse.events import SSEEvent

from meridian.models import (
    BigFiveScores,
    CandidateData,
    Confidence,
    EvidenceType,
    Flag,
    FlagCategory,
    Priority,
    Requirement,
    RubricAssessment,
    RubricLevel,
    ScenarioConfig,
    ScenarioName,
    ScenarioPriority,
    Valence,
)
from meridian.models.pipeline import (
    AssessmentMode,
    FlagProvenance,
    StageDOutput,
)

# ---------------------------------------------------------------------------
# Simple model builders
# ---------------------------------------------------------------------------


def make_scenario(name: ScenarioName = ScenarioName.DIGITAL_TRANSFORMATION) -> ScenarioConfig:
    """Build a minimal ScenarioConfig with no weight overrides."""
    return ScenarioConfig(name=name, category_weights={})


def make_requirement(req_id: str, *, assessable: bool = True) -> Requirement:
    """Build a minimal Requirement fixture."""
    return Requirement(
        requirement_id=req_id,
        text=f"Requirement {req_id}",
        source_quote=f"Source {req_id}",
        assessable_from_cv=assessable,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.LOW,
            growth=Priority.MEDIUM,
        ),
    )


def make_candidate(name: str, *, with_big_five: bool = True) -> CandidateData:
    """Build a minimal CandidateData fixture."""
    big_five = BigFiveScores(O=0.7, C=0.8, E=0.6, A=0.5, N=0.3) if with_big_five else None
    return CandidateData(
        name=name,
        cv_text=f"CV text for {name}",
        big_five=big_five,
        personality_source="manual" if with_big_five else None,
    )


def make_rubric_assessment(
    req_id: str,
    candidate: str,
    level: RubricLevel = RubricLevel.MEETS,
) -> RubricAssessment:
    """Build a minimal RubricAssessment fixture."""
    citation = f"Evidence for {candidate} / {req_id}" if level != RubricLevel.NOT_ASSESSABLE else None
    return RubricAssessment(
        requirement_id=req_id,
        candidate_name=candidate,
        rubric_level=level,
        confidence=Confidence.HIGH,
        cv_citation=citation,
    )


def make_cv_flag(req_id: str, candidate: str) -> Flag:
    """Build a minimal CV-derived Flag fixture."""
    return Flag(
        name="CV_EXCEEDS",
        candidate_name=candidate,
        category=FlagCategory.EXPERIENCE_STRENGTH,
        valence=Valence.POSITIVE,
        evidence_type=EvidenceType.CV_RUBRIC,
        requirement_id=req_id,
        rubric_level="exceeds",
        metadata={"active_priority": "high"},
    )


def make_personality_flag(candidate: str) -> Flag:
    """Build a minimal personality Flag fixture."""
    return Flag(
        name="EXECUTION_CONSCIENTIOUSNESS_FIT",
        candidate_name=candidate,
        category=FlagCategory.EXECUTION,
        valence=Valence.POSITIVE,
        evidence_type=EvidenceType.SCORED_FLAG,
        big_five_source="C",
        metadata={},
    )


def make_stage_d_output(
    candidates: list[CandidateData],
    requirements: list[Requirement],
    rubric_assessments: list[RubricAssessment],
    scenario: ScenarioConfig,
) -> StageDOutput:
    """Build a minimal StageDOutput fixture."""
    flags: list[Flag] = []
    provenance: dict[str, FlagProvenance] = {}
    for c in candidates:
        cv_flag = make_cv_flag(requirements[0].requirement_id, c.name)
        personality_flag = make_personality_flag(c.name)
        flags.extend([cv_flag, personality_flag])
        provenance[c.name] = FlagProvenance(
            assessment_mode=AssessmentMode.FULL if c.big_five else AssessmentMode.PARTIAL,
            personality_flag_count=1,
            cv_flag_count=1,
            total_flags=2,
            big_five_available=c.big_five is not None,
        )
    return StageDOutput(
        flags=flags,
        provenance_per_candidate=provenance,
        confirmed_requirements=requirements,
        candidate_data=candidates,
        rubric_matrix=rubric_assessments,
        scenario=scenario,
    )


# ---------------------------------------------------------------------------
# Async collection helper
# ---------------------------------------------------------------------------


async def collect(gen: AsyncIterator[SSEEvent]) -> list[SSEEvent]:
    """Drain an async generator into a list."""
    return [event async for event in gen]


# ---------------------------------------------------------------------------
# Mock factories for pipeline stages
# ---------------------------------------------------------------------------


def build_mock_requirements(count: int = 2) -> list[Requirement]:
    """Build ``count`` minimal requirements."""
    return [make_requirement(f"REQ-{i:02d}") for i in range(1, count + 1)]


def build_mock_rubric_assessments(
    candidates: list[CandidateData],
    requirements: list[Requirement],
) -> list[RubricAssessment]:
    """Build one rubric assessment per (candidate, requirement) pair."""
    return [
        make_rubric_assessment(req.requirement_id, c.name, RubricLevel.MEETS)
        for c in candidates
        for req in requirements
    ]


# ---------------------------------------------------------------------------
# LLM client mock builders
# ---------------------------------------------------------------------------


def build_full_pipeline_llm_client(
    requirements: list[Requirement],
    candidates: list[CandidateData],
) -> Any:
    """Build a MockLLMClient with responses for all pipeline LLM calls."""
    from meridian.common.llm_client import MockLLMClient

    c1_response = json.dumps(
        {
            "requirements": [
                {
                    "requirement_id": req.requirement_id,
                    "text": req.text,
                    "source_quote": req.source_quote,
                    "assessable_from_cv": req.assessable_from_cv,
                    "scenario_priority": {
                        "digital_transformation": "high",
                        "post_acquisition": "medium",
                        "turnaround": "medium",
                        "stabilization": "low",
                        "growth": "medium",
                    },
                }
                for req in requirements
            ]
        }
    )

    def _c3_response(candidate_name: str) -> str:
        return json.dumps(
            [
                {
                    "requirement_id": req.requirement_id,
                    "candidate_name": candidate_name,
                    "rubric_level": "meets",
                    "confidence": "high",
                    "cv_citation": f"Evidence for {candidate_name} / {req.requirement_id}",
                }
                for req in requirements
            ]
        )

    def _agent_response(agent_role: str, candidate_names: list[str]) -> str:
        return json.dumps(
            {
                "agent_role": agent_role,
                "claims": [
                    {
                        "text": f"Strong candidate signal for {candidate_names[0]}",
                        "evidence_basis": {
                            "type": "cv_rubric",
                            "reference": requirements[0].requirement_id,
                        },
                        "confidence": "high",
                        "candidate_name": candidate_names[0],
                    }
                ],
                "summary": f"Agent {agent_role}: overall assessment complete for all candidates.",
                "assessment_mode": "full",
                "unaddressed_flags": [],
            }
        )

    synthesis_response = json.dumps(
        {
            "trade_off_statement": "Candidates present distinct but complementary profiles.",
        }
    )

    candidate_names = [c.name for c in candidates]
    responses = (
        [c1_response]
        + [_c3_response(c.name) for c in candidates]
        + [_agent_response("role_fit", candidate_names)]
        + [_agent_response("team_dynamics", candidate_names)]
        + [_agent_response("risk", candidate_names)]
        + [synthesis_response]
    )
    return MockLLMClient(responses)


def build_switch_llm_client(
    requirements: list[Requirement],
    candidates: list[CandidateData],
) -> Any:
    """Build a MockLLMClient for scenario switch (no C1/C3 calls)."""
    from meridian.common.llm_client import MockLLMClient

    candidate_names = [c.name for c in candidates]

    def _agent_response(agent_role: str) -> str:
        return json.dumps(
            {
                "agent_role": agent_role,
                "claims": [
                    {
                        "text": f"Signal found for {candidate_names[0]}",
                        "evidence_basis": {
                            "type": "cv_rubric",
                            "reference": requirements[0].requirement_id,
                        },
                        "confidence": "high",
                        "candidate_name": candidate_names[0],
                    }
                ],
                "summary": f"Agent {agent_role}: assessment complete.",
                "assessment_mode": "full",
                "unaddressed_flags": [],
            }
        )

    synthesis_response = json.dumps(
        {
            "trade_off_statement": "Candidates evaluated under new scenario.",
        }
    )

    responses = [
        _agent_response("role_fit"),
        _agent_response("team_dynamics"),
        _agent_response("risk"),
        synthesis_response,
    ]
    return MockLLMClient(responses)


def build_cached_state(
    candidates: list[CandidateData],
    requirements: list[Requirement],
) -> Any:
    """Build a CachedPipelineState from pre-built data."""
    from meridian.evaluation.scenario_switch import CachedPipelineState

    rubric_assessments = build_mock_rubric_assessments(candidates, requirements)
    return CachedPipelineState(
        requirements=requirements,
        rubric_assessments=rubric_assessments,
        candidates=candidates,
        extraction_warnings=[],
    )
