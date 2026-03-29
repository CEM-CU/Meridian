"""Shared fixtures for Stage E integration tests.

Contains all test data construction helpers extracted from
test_stage_e_integration.py to keep the main test file under 800 lines.

Provides:
- _sp: ScenarioPriority builder
- _REQUIREMENTS: 8-item requirement list (6 CV + 2 behavioral)
- _CANDIDATES: 3 candidates (Alice/full, Bob/full, Carol/partial)
- _RUBRIC_MATRIX: 3x8 RubricAssessment list
- _FLAGS: 11 Flag objects
- _PROVENANCE: per-candidate FlagProvenance mapping
- _DIGITAL_SCENARIO / _GROWTH_SCENARIO: ScenarioConfig fixtures
- _TRADE_OFF_STATEMENT: canned synthesis statement
- _make_stage_d_output: StageDOutput factory
- _make_role_fit_verdict_json / _make_team_dynamics_verdict_json
  / _make_risk_verdict_json: canned AgentVerdict JSON factories
- _MockLLMClient / _SlowAgentMockLLMClient: mock LLM implementations
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from meridian.models.candidates import BigFiveScores, CandidateData
from meridian.models.flags import EvidenceType, Flag, FlagCategory, Valence
from meridian.models.pipeline import AssessmentMode, FlagProvenance, StageDOutput
from meridian.models.requirements import Priority, Requirement, ScenarioPriority
from meridian.models.rubric import Confidence, RubricAssessment, RubricLevel
from meridian.models.scenarios import ScenarioConfig, ScenarioName

# ---------------------------------------------------------------------------
# Shared scenario priority helpers
# ---------------------------------------------------------------------------


def _sp(
    digital: Priority = Priority.MEDIUM,
    post_acq: Priority = Priority.MEDIUM,
    turnaround: Priority = Priority.MEDIUM,
    stabilization: Priority = Priority.MEDIUM,
    growth: Priority = Priority.MEDIUM,
) -> ScenarioPriority:
    """Build a ScenarioPriority from keyword arguments."""
    return ScenarioPriority(
        digital_transformation=digital,
        post_acquisition=post_acq,
        turnaround=turnaround,
        stabilization=stabilization,
        growth=growth,
    )


# ---------------------------------------------------------------------------
# Requirement fixtures
# 6 CV-assessable + 2 behavioral = 8 total
# ---------------------------------------------------------------------------

_REQUIREMENTS: list[Requirement] = [
    Requirement(
        requirement_id="REQ-01",
        text="15+ years of technology leadership experience",
        source_quote="15+ years of technology leadership experience",
        assessable_from_cv=True,
        scenario_priority=_sp(digital=Priority.HIGH, turnaround=Priority.HIGH),
    ),
    Requirement(
        requirement_id="REQ-02",
        text="Proven P&L management of $200M+",
        source_quote="Proven P&L management of $200M+",
        assessable_from_cv=True,
        scenario_priority=_sp(
            digital=Priority.MEDIUM,
            post_acq=Priority.HIGH,
            turnaround=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-03",
        text="Digital transformation programme delivery",
        source_quote="Digital transformation programme delivery",
        assessable_from_cv=True,
        scenario_priority=_sp(
            digital=Priority.HIGH,
            post_acq=Priority.LOW,
            turnaround=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-04",
        text="Cross-functional stakeholder management",
        source_quote="Cross-functional stakeholder management",
        assessable_from_cv=True,
        scenario_priority=_sp(
            digital=Priority.MEDIUM,
            post_acq=Priority.HIGH,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-05",
        text="Enterprise cloud migration experience",
        source_quote="Enterprise cloud migration experience",
        assessable_from_cv=True,
        scenario_priority=_sp(digital=Priority.HIGH, growth=Priority.MEDIUM),
    ),
    Requirement(
        requirement_id="REQ-06",
        text="International market expansion track record",
        source_quote="International market expansion track record",
        assessable_from_cv=True,
        scenario_priority=_sp(growth=Priority.HIGH, post_acq=Priority.MEDIUM),
    ),
    # Behavioral requirements — NOT assessable from CV
    Requirement(
        requirement_id="REQ-07",
        text="Builds psychological safety in executive teams",
        source_quote="Builds psychological safety in executive teams",
        assessable_from_cv=False,
        scenario_priority=_sp(),
    ),
    Requirement(
        requirement_id="REQ-08",
        text="Navigates ambiguity and board-level pressure",
        source_quote="Navigates ambiguity and board-level pressure",
        assessable_from_cv=False,
        scenario_priority=_sp(),
    ),
]

# ---------------------------------------------------------------------------
# Candidate fixtures
# Alice and Bob: full mode (Big Five available)
# Carol: partial mode (no Big Five)
# ---------------------------------------------------------------------------

_ALICE = CandidateData(
    name="Alice",
    cv_text=(
        "Alice has 18 years technology leadership at AcmeCorp, including $350M P&L responsibility. "
        "Led three digital transformation programmes at AcmeCorp from 2018-2022. "
        "Managed enterprise cloud migration (AWS, Azure) across six countries. "
        "Stakeholder management across 12 business units. "
        "Expanded into APAC markets for GlobalFirm."
    ),
    big_five=BigFiveScores(O=0.82, C=0.75, E=0.65, A=0.58, N=0.28),
    personality_source="Big Five Manual",
)

_BOB = CandidateData(
    name="Bob",
    cv_text=(
        "Bob has 12 years in technology roles at StartupX. "
        "P&L of $90M at StartupX. "
        "Led digital-adjacent projects at StartupX. "
        "Limited cross-functional exposure documented in CV."
    ),
    big_five=BigFiveScores(O=0.60, C=0.85, E=0.72, A=0.45, N=0.42),
    personality_source="Big Five Manual",
)

_CAROL = CandidateData(
    name="Carol",
    cv_text=(
        "Carol has 20 years in finance transformation at MegaBank. "
        "P&L of $500M at MegaBank. "
        "Led major ERP and cloud platform deployments. "
        "International expansion into EMEA."
    ),
    big_five=None,  # partial mode — no personality data
    personality_source=None,
)

_CANDIDATES: list[CandidateData] = [_ALICE, _BOB, _CAROL]

# ---------------------------------------------------------------------------
# Rubric assessment matrix: 3 candidates x 8 requirements
# ---------------------------------------------------------------------------


def _rubric(
    req_id: str,
    candidate: str,
    level: RubricLevel,
    conf: Confidence = Confidence.HIGH,
    citation: str | None = None,
    inv_q: str | None = None,
) -> RubricAssessment:
    """Build a RubricAssessment with sensible defaults."""
    return RubricAssessment(
        requirement_id=req_id,
        candidate_name=candidate,
        rubric_level=level,
        confidence=conf,
        cv_citation=citation,
        investigation_question=inv_q,
    )


_RUBRIC_MATRIX: list[RubricAssessment] = [
    # Alice
    _rubric("REQ-01", "Alice", RubricLevel.EXCEEDS, citation="18 years technology leadership at AcmeCorp"),
    _rubric("REQ-02", "Alice", RubricLevel.EXCEEDS, citation="$350M P&L responsibility"),
    _rubric("REQ-03", "Alice", RubricLevel.EXCEEDS, citation="three digital transformation programmes at AcmeCorp"),
    _rubric("REQ-04", "Alice", RubricLevel.MEETS, citation="Stakeholder management across 12 business units"),
    _rubric("REQ-05", "Alice", RubricLevel.EXCEEDS, citation="enterprise cloud migration across six countries"),
    _rubric("REQ-06", "Alice", RubricLevel.MEETS, citation="Expanded into APAC markets for GlobalFirm"),
    _rubric("REQ-07", "Alice", RubricLevel.NOT_ASSESSABLE),
    _rubric("REQ-08", "Alice", RubricLevel.NOT_ASSESSABLE),
    # Bob
    _rubric("REQ-01", "Bob", RubricLevel.PARTIAL, conf=Confidence.MEDIUM, citation="12 years in technology roles"),
    _rubric(
        "REQ-02",
        "Bob",
        RubricLevel.GAP,
        conf=Confidence.HIGH,
        inv_q="P&L only $90M — probed on scale-up to $200M+?",
    ),
    _rubric("REQ-03", "Bob", RubricLevel.PARTIAL, conf=Confidence.MEDIUM, citation="digital-adjacent projects"),
    _rubric(
        "REQ-04",
        "Bob",
        RubricLevel.GAP,
        conf=Confidence.HIGH,
        inv_q="Limited cross-functional exposure documented",
    ),
    _rubric("REQ-05", "Bob", RubricLevel.NOT_ASSESSABLE),
    _rubric("REQ-06", "Bob", RubricLevel.GAP, conf=Confidence.HIGH, inv_q="No international track record in CV"),
    _rubric("REQ-07", "Bob", RubricLevel.NOT_ASSESSABLE),
    _rubric("REQ-08", "Bob", RubricLevel.NOT_ASSESSABLE),
    # Carol
    _rubric("REQ-01", "Carol", RubricLevel.EXCEEDS, citation="20 years in finance transformation at MegaBank"),
    _rubric("REQ-02", "Carol", RubricLevel.EXCEEDS, citation="$500M P&L at MegaBank"),
    _rubric("REQ-03", "Carol", RubricLevel.MEETS, citation="ERP and cloud platform deployments"),
    _rubric("REQ-04", "Carol", RubricLevel.MEETS),
    _rubric("REQ-05", "Carol", RubricLevel.MEETS, citation="cloud platform deployments"),
    _rubric("REQ-06", "Carol", RubricLevel.MEETS, citation="International expansion into EMEA"),
    _rubric("REQ-07", "Carol", RubricLevel.NOT_ASSESSABLE),
    _rubric("REQ-08", "Carol", RubricLevel.NOT_ASSESSABLE),
]

# ---------------------------------------------------------------------------
# Flag fixtures — 10+ flags covering personality + CV evidence types
# ---------------------------------------------------------------------------


def _make_flag(
    name: str,
    candidate: str,
    category: FlagCategory,
    valence: Valence,
    evidence_type: EvidenceType,
    *,
    big_five_source: str | None = None,
    requirement_id: str | None = None,
    rubric_level: str | None = None,
    topic_keywords: list[str] | None = None,
) -> Flag:
    """Construct a Flag with required fields."""
    return Flag(
        name=name,
        candidate_name=candidate,
        category=category,
        valence=valence,
        evidence_type=evidence_type,
        big_five_source=big_five_source,
        requirement_id=requirement_id,
        rubric_level=rubric_level,
        topic_keywords=topic_keywords or [],
    )


_FLAGS: list[Flag] = [
    # Alice — personality flags (full mode)
    _make_flag(
        "EXECUTION_CONSCIENTIOUSNESS_FIT",
        "Alice",
        FlagCategory.EXECUTION,
        Valence.POSITIVE,
        EvidenceType.SCORED_FLAG,
        big_five_source="C",
        topic_keywords=["conscientiousness", "execution", "delivery"],
    ),
    _make_flag(
        "STRATEGIC_OPENNESS_FIT",
        "Alice",
        FlagCategory.STRATEGIC,
        Valence.POSITIVE,
        EvidenceType.SCORED_FLAG,
        big_five_source="O",
        topic_keywords=["openness", "strategic", "innovation"],
    ),
    # Alice — CV flags
    _make_flag(
        "CV_EXCEEDS",
        "Alice",
        FlagCategory.EXPERIENCE_STRENGTH,
        Valence.POSITIVE,
        EvidenceType.CV_RUBRIC,
        requirement_id="REQ-01",
        rubric_level="exceeds",
        topic_keywords=["technology", "leadership"],
    ),
    _make_flag(
        "CV_EXCEEDS",
        "Alice",
        FlagCategory.EXPERIENCE_STRENGTH,
        Valence.POSITIVE,
        EvidenceType.CV_RUBRIC,
        requirement_id="REQ-03",
        rubric_level="exceeds",
        topic_keywords=["digital", "transformation"],
    ),
    # Bob — personality flags (full mode)
    _make_flag(
        "DERAILMENT_NEUROTICISM_UNDER_STRESS",
        "Bob",
        FlagCategory.DERAILMENT,
        Valence.NEGATIVE,
        EvidenceType.SCORED_FLAG,
        big_five_source="N",
        topic_keywords=["neuroticism", "stress", "derailment"],
    ),
    _make_flag(
        "EXECUTION_CONSCIENTIOUSNESS_FIT",
        "Bob",
        FlagCategory.EXECUTION,
        Valence.POSITIVE,
        EvidenceType.SCORED_FLAG,
        big_five_source="C",
        topic_keywords=["conscientiousness", "execution"],
    ),
    # Bob — CV flags (gaps)
    _make_flag(
        "CV_GAP",
        "Bob",
        FlagCategory.EXPERIENCE_GAP,
        Valence.NEGATIVE,
        EvidenceType.REQUIREMENT_GAP,
        requirement_id="REQ-02",
        rubric_level="gap",
        topic_keywords=["P&L", "management", "scale"],
    ),
    _make_flag(
        "CV_GAP",
        "Bob",
        FlagCategory.EXPERIENCE_GAP,
        Valence.NEGATIVE,
        EvidenceType.REQUIREMENT_GAP,
        requirement_id="REQ-04",
        rubric_level="gap",
        topic_keywords=["stakeholder", "cross-functional"],
    ),
    # Carol — no personality flags (partial mode)
    _make_flag(
        "CV_EXCEEDS",
        "Carol",
        FlagCategory.EXPERIENCE_STRENGTH,
        Valence.POSITIVE,
        EvidenceType.CV_RUBRIC,
        requirement_id="REQ-02",
        rubric_level="exceeds",
        topic_keywords=["P&L", "finance", "management"],
    ),
    _make_flag(
        "CV_EXCEEDS",
        "Carol",
        FlagCategory.EXPERIENCE_STRENGTH,
        Valence.POSITIVE,
        EvidenceType.CV_RUBRIC,
        requirement_id="REQ-01",
        rubric_level="exceeds",
        topic_keywords=["leadership", "transformation"],
    ),
    # Extra flag to ensure >10 total
    _make_flag(
        "DARK_SIDE_LOW_AGREEABLENESS",
        "Bob",
        FlagCategory.DARK_SIDE,
        Valence.NEGATIVE,
        EvidenceType.SCORED_FLAG,
        big_five_source="A",
        topic_keywords=["agreeableness", "dark_side", "conflict"],
    ),
]

# ---------------------------------------------------------------------------
# Provenance per candidate
# ---------------------------------------------------------------------------

_PROVENANCE: dict[str, FlagProvenance] = {
    "Alice": FlagProvenance(
        assessment_mode=AssessmentMode.FULL,
        personality_flag_count=2,
        cv_flag_count=2,
        total_flags=4,
        big_five_available=True,
        personality_source="Big Five Manual",
        requirements_assessed=6,
        high_priority_gap_count=0,
    ),
    "Bob": FlagProvenance(
        assessment_mode=AssessmentMode.FULL,
        personality_flag_count=3,
        cv_flag_count=2,
        total_flags=5,
        big_five_available=True,
        personality_source="Big Five Manual",
        requirements_assessed=6,
        high_priority_gap_count=2,
    ),
    "Carol": FlagProvenance(
        assessment_mode=AssessmentMode.PARTIAL,
        personality_flag_count=0,
        cv_flag_count=2,
        total_flags=2,
        big_five_available=False,
        personality_source=None,
        requirements_assessed=6,
        high_priority_gap_count=0,
    ),
}

# ---------------------------------------------------------------------------
# Scenario fixtures
# ---------------------------------------------------------------------------

_DIGITAL_SCENARIO = ScenarioConfig(
    name=ScenarioName.DIGITAL_TRANSFORMATION,
    category_weights={
        "EXECUTION": 1.2,
        "STRATEGIC": 1.3,
        "EXPERIENCE_STRENGTH": 1.2,
        "EXPERIENCE_GAP": 1.1,
    },
)

_GROWTH_SCENARIO = ScenarioConfig(
    name=ScenarioName.GROWTH,
    category_weights={
        "EXPERIENCE_STRENGTH": 0.9,
        "EXPERIENCE_GAP": 0.8,
    },
)


def _make_stage_d_output(scenario: ScenarioConfig = _DIGITAL_SCENARIO) -> StageDOutput:
    """Construct a realistic StageDOutput using only shared.models primitives."""
    return StageDOutput(
        flags=_FLAGS,
        provenance_per_candidate=_PROVENANCE,
        confirmed_requirements=_REQUIREMENTS,
        candidate_data=_CANDIDATES,
        rubric_matrix=_RUBRIC_MATRIX,
        scenario=scenario,
    )


# ---------------------------------------------------------------------------
# Canned AgentVerdict JSON per agent role
# Each verdict covers all three candidates to ensure summaries are built.
# Evidence references are intentionally confined to valid flag names /
# requirement IDs so the audit passes cleanly.
# ---------------------------------------------------------------------------

_TRADE_OFF_STATEMENT = (
    "Alice leads on technology leadership and digital transformation, while Carol offers superior "
    "P&L credentials and operational scale. Bob presents material gaps on both P&L management and "
    "stakeholder management, alongside elevated risk signals. The committee should weigh Alice's "
    "depth of transformation experience against Carol's financial stewardship track record."
)


def _make_role_fit_verdict_json() -> str:
    """Return valid role_fit AgentVerdict JSON covering all three candidates."""
    return json.dumps(
        {
            "agent_role": "role_fit",
            "summary": (
                "Alice demonstrates the strongest fit for the role, exceeding requirements on technology "
                "leadership and digital transformation. Carol meets most requirements with excellent P&L "
                "credentials. Bob shows partial alignment with gaps on scale."
            ),
            "assessment_mode": "full",
            "unaddressed_flags": [],
            "claims": [
                {
                    "text": "Alice exceeds the technology leadership requirement with 18 years of experience.",
                    "evidence_basis": {"type": "cv_rubric", "reference": "REQ-01"},
                    "confidence": "high",
                    "candidate_name": "Alice",
                },
                {
                    "text": "Alice demonstrates strong digital transformation programme delivery.",
                    "evidence_basis": {"type": "cv_rubric", "reference": "REQ-03"},
                    "confidence": "high",
                    "candidate_name": "Alice",
                },
                {
                    "text": "Carol meets the P&L management requirement with $500M responsibility.",
                    "evidence_basis": {"type": "cv_rubric", "reference": "REQ-02"},
                    "confidence": "high",
                    "candidate_name": "Carol",
                },
                {
                    "text": "Bob shows only partial alignment on technology leadership tenure.",
                    "evidence_basis": {"type": "cv_rubric", "reference": "REQ-01"},
                    "confidence": "medium",
                    "candidate_name": "Bob",
                },
            ],
        }
    )


def _make_team_dynamics_verdict_json() -> str:
    """Return valid team_dynamics AgentVerdict JSON covering all three candidates."""
    return json.dumps(
        {
            "agent_role": "team_dynamics",
            "summary": (
                "No significant collision risks detected for Alice or Carol under digital transformation "
                "scenario. Bob's profile suggests potential friction dynamics under sustained pressure."
            ),
            "assessment_mode": "full",
            "unaddressed_flags": [],
            "claims": [
                {
                    "text": "Alice shows complementary extraversion balance with the existing team.",
                    "evidence_basis": {"type": "biographical_pattern", "reference": "team_complementarity"},
                    "confidence": "medium",
                    "candidate_name": "Alice",
                },
                {
                    "text": "Bob shows potential friction with team dynamics based on career trajectory patterns.",
                    "evidence_basis": {"type": "biographical_pattern", "reference": "team_friction_pattern"},
                    "confidence": "medium",
                    "candidate_name": "Bob",
                },
                {
                    "text": "Carol — insufficient personality data for team dynamics assessment.",
                    "evidence_basis": {"type": "biographical_pattern", "reference": "partial_mode_limitation"},
                    "confidence": "low",
                    "candidate_name": "Carol",
                },
            ],
        }
    )


def _make_risk_verdict_json() -> str:
    """Return valid risk AgentVerdict JSON covering all three candidates."""
    return json.dumps(
        {
            "agent_role": "risk",
            "summary": (
                "Bob carries derailment risk driven by elevated neuroticism under stress and low "
                "agreeableness. Alice and Carol present low risk profiles based on available evidence."
            ),
            "assessment_mode": "full",
            "unaddressed_flags": [],
            "claims": [
                {
                    "text": "Bob presents derailment risk under stress based on elevated neuroticism score.",
                    "evidence_basis": {"type": "scored_flag", "reference": "DERAILMENT_NEUROTICISM_UNDER_STRESS"},
                    "confidence": "high",
                    "candidate_name": "Bob",
                },
                {
                    "text": "Bob shows dark-side risk from low agreeableness pattern.",
                    "evidence_basis": {"type": "scored_flag", "reference": "DARK_SIDE_LOW_AGREEABLENESS"},
                    "confidence": "medium",
                    "candidate_name": "Bob",
                },
                {
                    "text": "Bob has a significant experience gap on P&L management at the required scale.",
                    "evidence_basis": {"type": "requirement_gap", "reference": "REQ-02"},
                    "confidence": "high",
                    "candidate_name": "Bob",
                },
                {
                    "text": "Alice presents low derailment risk based on stable career trajectory and no red flags.",
                    "evidence_basis": {"type": "biographical_pattern", "reference": "career_stability"},
                    "confidence": "high",
                    "candidate_name": "Alice",
                },
            ],
        }
    )


# ---------------------------------------------------------------------------
# Mock LLM clients
# ---------------------------------------------------------------------------


class _MockLLMClient:
    """Routing mock LLM client for Stage E integration tests.

    Routes by inspecting the system prompt to identify which agent / synthesis
    call is being made, then returns appropriate canned JSON / text.

    Agent identification:
    - "the researcher"         → role_fit agent
    - "devil's advocate"       → team_dynamics agent
    - "risk analyst"           → risk agent
    - anything else            → trade-off statement (synthesis)

    Tracks call history for post-test assertions.
    """

    def __init__(self, trade_off_statement: str = _TRADE_OFF_STATEMENT) -> None:
        self._trade_off_statement = trade_off_statement
        self.calls: list[tuple[str, str]] = []

    async def complete(
        self,
        system: str,
        user: str,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Return canned agent JSON or synthesis statement based on system prompt."""
        self.calls.append((system, user))
        s = system.lower()

        if "the researcher" in s:
            return _make_role_fit_verdict_json()
        if "devil's advocate" in s:
            return _make_team_dynamics_verdict_json()
        if "risk analyst" in s:
            return _make_risk_verdict_json()
        # Synthesis trade-off statement call
        return self._trade_off_statement


class _SlowAgentMockLLMClient(_MockLLMClient):
    """Mock LLM where the team_dynamics agent is intentionally slow (exceeds timeout).

    All other agents respond instantly with valid JSON.
    The team_dynamics coroutine sleeps longer than the per-agent timeout so
    that the runner's asyncio.wait_for fires and returns None for that agent.
    """

    def __init__(self, slow_role: str = "devil's advocate", delay: float = 30.0) -> None:
        super().__init__()
        self._slow_role = slow_role
        self._delay = delay

    async def complete(
        self,
        system: str,
        user: str,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Inject a sleep on the designated slow agent call."""
        s = system.lower()
        if self._slow_role in s:
            await asyncio.sleep(self._delay)
        return await super().complete(system, user, response_format)
