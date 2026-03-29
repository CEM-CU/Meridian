"""Shared test helpers for Stage C CV assessment tests.

Provides the mock LLM client and factory helpers used across multiple test files.
Not a test file itself — no test functions defined here.
"""

from __future__ import annotations

from typing import Any

from meridian.models import (
    BigFiveScores,
    CandidateData,
    Confidence,
    Priority,
    Requirement,
    RubricAssessment,
    RubricLevel,
    ScenarioConfig,
    ScenarioName,
    ScenarioPriority,
)


class MockLLMClient:
    """Mock LLM client for testing. Returns canned responses in round-robin order."""

    def __init__(self, responses: list[str]) -> None:
        """Initialise with a list of canned responses (cycled round-robin)."""
        self.responses = responses
        self.call_count = 0
        self.calls: list[tuple[str, str]] = []

    async def complete(self, system: str, user: str, response_format: dict | None = None) -> str:
        """Return the next canned response and record the call."""
        self.calls.append((system, user))
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return response


def make_scenario_priority(
    dt: str = "high",
    pa: str = "medium",
    ta: str = "low",
    st_: str = "medium",
    gr: str = "high",
) -> ScenarioPriority:
    """Create a ScenarioPriority with convenient defaults."""
    return ScenarioPriority(
        digital_transformation=Priority(dt),
        post_acquisition=Priority(pa),
        turnaround=Priority(ta),
        stabilization=Priority(st_),
        growth=Priority(gr),
    )


def make_requirement(
    req_id: str = "REQ-01",
    text: str = "10+ years technology leadership experience",
    source_quote: str = "Requires 10+ years of technology leadership",
    assessable: bool = True,
    scenario_priority: ScenarioPriority | None = None,
) -> Requirement:
    """Create a Requirement with sensible defaults."""
    return Requirement(
        requirement_id=req_id,
        text=text,
        source_quote=source_quote,
        assessable_from_cv=assessable,
        scenario_priority=scenario_priority or make_scenario_priority(),
    )


def make_assessment_dict(
    requirement_id: str = "REQ-01",
    candidate_name: str = "Alice",
    rubric_level: str = "meets",
    confidence: str = "high",
    cv_citation: str | None = "Managed 300-person engineering organisation",
    cv_location: str | None = "CTO role, 2019-present",
    notes: str | None = None,
    investigation_question: str | None = None,
) -> dict[str, Any]:
    """Create a valid assessment dict for JSON response simulation."""
    return {
        "requirement_id": requirement_id,
        "candidate_name": candidate_name,
        "rubric_level": rubric_level,
        "confidence": confidence,
        "cv_citation": cv_citation,
        "cv_location": cv_location,
        "notes": notes,
        "investigation_question": investigation_question,
    }


def make_scenario(name: ScenarioName = ScenarioName.DIGITAL_TRANSFORMATION) -> ScenarioConfig:
    """Create a ScenarioConfig."""
    return ScenarioConfig(name=name)


def make_candidate(
    name: str = "Alice",
    cv_text: str = "Experienced technology leader with 15 years of engineering leadership.",
) -> CandidateData:
    """Create a minimal CandidateData."""
    return CandidateData(
        name=name,
        cv_text=cv_text,
        big_five=BigFiveScores(O=0.7, C=0.8, E=0.6, A=0.5, N=0.3),
    )


def make_rubric_assessment(
    req_id: str = "REQ-01",
    candidate: str = "Alice",
    level: RubricLevel = RubricLevel.MEETS,
    confidence: Confidence = Confidence.HIGH,
    cv_citation: str | None = "Led a 300-person organisation",
    cv_location: str | None = "CTO role",
) -> RubricAssessment:
    """Create a RubricAssessment with sensible defaults."""
    return RubricAssessment(
        requirement_id=req_id,
        candidate_name=candidate,
        rubric_level=level,
        confidence=confidence,
        cv_citation=cv_citation,
        cv_location=cv_location,
    )
