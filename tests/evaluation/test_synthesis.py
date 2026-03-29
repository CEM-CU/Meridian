"""Tests for E7: Synthesis Template — trade-off matrix, candidate summaries,
contested signals, provenance header, epistemic disclaimers, and assembler.

All tests are deterministic (no real LLM calls). The MockLLMClient from
shared.llm_client is used for the trade-off statement test.
"""

from __future__ import annotations

from typing import Any

import pytest

from meridian.evaluation.layer1_signals import Layer1Output, TensionPair
from meridian.evaluation.schemas import AgentVerdict, Claim, EvidenceBasis
from meridian.evaluation.synthesis.assembler import assemble_synthesis
from meridian.evaluation.synthesis.builder import (
    build_candidate_summaries,
    build_epistemic_disclaimers,
    build_provenance_header,
    build_trade_off_matrix,
    detect_contested_signals,
)
from meridian.evaluation.synthesis.models import (
    CandidateSummary,
    SynthesisOutput,
    TradeOffCell,
)
from meridian.evaluation.synthesis.trade_off_statement import generate_trade_off_statement
from meridian.models import (
    AssessmentMode,
    Confidence,
    FlagProvenance,
    Priority,
    Requirement,
    RubricAssessment,
    RubricLevel,
    ScenarioConfig,
    ScenarioName,
    ScenarioPriority,
    StageDOutput,
)
from meridian.models.candidates import CandidateData
from meridian.models.flags import EvidenceType, Flag, FlagCategory, Valence

# ---------------------------------------------------------------------------
# Helpers / builders
# ---------------------------------------------------------------------------


def _scenario(name: ScenarioName = ScenarioName.DIGITAL_TRANSFORMATION) -> ScenarioConfig:
    return ScenarioConfig(name=name, category_weights={})


def _req(
    req_id: str,
    *,
    assessable: bool = True,
    dt_priority: Priority = Priority.HIGH,
    stab_priority: Priority = Priority.LOW,
) -> Requirement:
    return Requirement(
        requirement_id=req_id,
        text=f"Requirement text for {req_id}",
        source_quote=f"Source quote for {req_id}",
        assessable_from_cv=assessable,
        scenario_priority=ScenarioPriority(
            digital_transformation=dt_priority,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=stab_priority,
            growth=Priority.MEDIUM,
        ),
    )


def _assessment(
    req_id: str,
    candidate: str,
    level: RubricLevel = RubricLevel.MEETS,
    confidence: Confidence = Confidence.HIGH,
    *,
    investigation_question: str | None = None,
    cv_citation: str | None = "Some CV citation",
) -> RubricAssessment:
    return RubricAssessment(
        requirement_id=req_id,
        candidate_name=candidate,
        rubric_level=level,
        confidence=confidence,
        cv_citation=cv_citation,
        investigation_question=investigation_question,
    )


def _claim(
    candidate: str,
    ref: str = "FLAG_A",
    evidence_type: str = "scored_flag",
    confidence: str = "high",
    text: str | None = None,
) -> Claim:
    return Claim(
        text=text or f"Claim about {candidate} referencing {ref} for role performance assessment",
        evidence_basis=EvidenceBasis(type=evidence_type, reference=ref),  # type: ignore[arg-type]
        confidence=confidence,
        candidate_name=candidate,
    )


def _verdict(
    role: str,
    claims: list[Claim],
    mode: str = "full",
    summary: str | None = None,
    unaddressed: list[str] | None = None,
) -> AgentVerdict:
    return AgentVerdict(
        agent_role=role,
        claims=claims,
        summary=summary or f"Summary for {role} agent covering all candidate assessments in this evaluation cycle.",
        assessment_mode=mode,
        unaddressed_flags=unaddressed or [],
    )


def _flag(
    name: str,
    candidate: str,
    category: FlagCategory,
    valence: Valence,
    evidence_type: EvidenceType = EvidenceType.SCORED_FLAG,
) -> Flag:
    return Flag(
        name=name,
        candidate_name=candidate,
        category=category,
        valence=valence,
        evidence_type=evidence_type,
    )


def _provenance(
    mode: AssessmentMode = AssessmentMode.FULL,
    total_flags: int = 5,
    personality_source: str | None = "Big Five Manual",
) -> FlagProvenance:
    return FlagProvenance(
        assessment_mode=mode,
        personality_flag_count=2,
        cv_flag_count=3,
        total_flags=total_flags,
        big_five_available=(mode == AssessmentMode.FULL),
        personality_source=personality_source,
        requirements_assessed=5,
        high_priority_gap_count=1,
    )


def _candidate_data(name: str) -> CandidateData:
    return CandidateData(name=name, cv_text=f"CV text for {name}")


def _stage_d_output(
    candidates: list[str] | None = None,
    requirements: list[Requirement] | None = None,
    rubric_assessments: list[RubricAssessment] | None = None,
    scenario: ScenarioConfig | None = None,
    modes: dict[str, AssessmentMode] | None = None,
) -> StageDOutput:
    candidates = candidates or ["Alice", "Bob"]
    reqs = requirements or [_req("REQ-01"), _req("REQ-02", dt_priority=Priority.LOW)]
    assessments = rubric_assessments or [_assessment("REQ-01", c) for c in candidates] + [
        _assessment("REQ-02", c) for c in candidates
    ]
    sc = scenario or _scenario()
    modes_map = modes or {c: AssessmentMode.FULL for c in candidates}
    return StageDOutput(
        flags=[],
        provenance_per_candidate={c: _provenance(modes_map.get(c, AssessmentMode.FULL)) for c in candidates},
        confirmed_requirements=reqs,
        candidate_data=[_candidate_data(c) for c in candidates],
        rubric_matrix=assessments,
        scenario=sc,
    )


def _layer1_output(tension_map: list[TensionPair] | None = None) -> Layer1Output:
    return Layer1Output(
        weighted_scores_per_candidate={},
        signal_labels={},
        risk_bands={},
        tension_map=tension_map or [],
        partial_mode_notes=[],
    )


class _MockLLMClient:
    """Minimal mock LLM client for synthesis tests."""

    _DEFAULT_RESPONSE = (
        "Candidate A offers deep technical experience. "
        "Candidate B offers broader industry reach. "
        "Both present distinct trade-offs worth committee deliberation."
    )

    def __init__(self, response: str = _DEFAULT_RESPONSE) -> None:
        self._response = response

    async def complete(
        self,
        system: str,
        user: str,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        return self._response


# ---------------------------------------------------------------------------
# Test 1: Trade-off matrix — correct cells, sorted by priority (high first)
# ---------------------------------------------------------------------------


class TestTradeOffMatrix:
    """Trade-off matrix builder tests."""

    def test_cells_sorted_high_priority_first(self) -> None:
        """High-priority rows appear before low-priority rows."""
        reqs = [
            _req("REQ-01", dt_priority=Priority.LOW),
            _req("REQ-02", dt_priority=Priority.HIGH),
        ]
        assessments = [
            _assessment("REQ-01", "Alice"),
            _assessment("REQ-02", "Alice"),
        ]
        scenario = _scenario(ScenarioName.DIGITAL_TRANSFORMATION)
        matrix = build_trade_off_matrix(
            rubric_assessments=assessments,
            requirements=reqs,
            scenario=scenario,
            assessment_modes={"Alice": "full"},
        )
        priorities = [cell.active_priority for cell in matrix]
        # HIGH before LOW
        assert priorities.index("high") < priorities.index("low")

    def test_cells_contain_correct_rubric_levels(self) -> None:
        """Each cell reflects the rubric assessment for that requirement x candidate."""
        reqs = [_req("REQ-01")]
        assessments = [_assessment("REQ-01", "Alice", RubricLevel.EXCEEDS)]
        matrix = build_trade_off_matrix(
            rubric_assessments=assessments,
            requirements=reqs,
            scenario=_scenario(),
            assessment_modes={"Alice": "full"},
        )
        assert len(matrix) == 1
        assert matrix[0].rubric_level == "exceeds"
        assert matrix[0].candidate_name == "Alice"
        assert matrix[0].requirement_id == "REQ-01"

    def test_cells_include_cv_citation(self) -> None:
        """CV citation is passed through to the cell."""
        reqs = [_req("REQ-01")]
        assessments = [_assessment("REQ-01", "Alice", cv_citation="PhD Stanford 2011")]
        matrix = build_trade_off_matrix(
            rubric_assessments=assessments,
            requirements=reqs,
            scenario=_scenario(),
            assessment_modes={"Alice": "full"},
        )
        assert matrix[0].cv_citation == "PhD Stanford 2011"

    def test_unknown_requirement_id_skipped(self) -> None:
        """Assessments referencing a requirement not in the list are silently skipped."""
        reqs = [_req("REQ-01")]
        assessments = [
            _assessment("REQ-01", "Alice"),
            _assessment("REQ-99", "Alice"),  # unknown
        ]
        matrix = build_trade_off_matrix(
            rubric_assessments=assessments,
            requirements=reqs,
            scenario=_scenario(),
            assessment_modes={"Alice": "full"},
        )
        req_ids = [c.requirement_id for c in matrix]
        assert "REQ-99" not in req_ids
        assert "REQ-01" in req_ids


# ---------------------------------------------------------------------------
# Test 2: Partial mode → behavioral rows show "not_assessable"
# ---------------------------------------------------------------------------


class TestTradeOffMatrixPartialMode:
    """Partial mode: non-CV-assessable requirements show not_assessable."""

    def test_behavioral_rows_not_assessable_in_partial_mode(self) -> None:
        """Behavioral (assessable_from_cv=False) rows become not_assessable for partial candidates."""
        reqs = [
            _req("REQ-01", assessable=True),
            _req("REQ-11", assessable=False),
        ]
        assessments = [
            _assessment("REQ-01", "Alice", RubricLevel.MEETS),
            _assessment("REQ-11", "Alice", RubricLevel.PARTIAL),
        ]
        matrix = build_trade_off_matrix(
            rubric_assessments=assessments,
            requirements=reqs,
            scenario=_scenario(),
            assessment_modes={"Alice": "partial"},
        )
        cells_by_req = {c.requirement_id: c for c in matrix}
        # CV-assessable: keep original rubric level
        assert cells_by_req["REQ-01"].rubric_level == "meets"
        # Behavioral: forced to not_assessable
        assert cells_by_req["REQ-11"].rubric_level == "not_assessable"

    def test_cv_assessable_rows_unchanged_in_partial_mode(self) -> None:
        """CV-assessable rows are not affected by partial mode."""
        reqs = [_req("REQ-01", assessable=True)]
        assessments = [_assessment("REQ-01", "Alice", RubricLevel.EXCEEDS)]
        matrix = build_trade_off_matrix(
            rubric_assessments=assessments,
            requirements=reqs,
            scenario=_scenario(),
            assessment_modes={"Alice": "partial"},
        )
        assert matrix[0].rubric_level == "exceeds"


# ---------------------------------------------------------------------------
# Test 3: Candidate summaries — all candidates present, highlights populated
# ---------------------------------------------------------------------------


class TestCandidateSummaries:
    """Candidate summaries include all candidates and agent highlights."""

    def test_all_candidates_present(self) -> None:
        """Summary list contains one entry per candidate."""
        verdicts = {
            "role_fit": _verdict("role_fit", [_claim("Alice"), _claim("Bob")]),
        }
        summaries = build_candidate_summaries(
            verdicts=verdicts,
            tension_map=[],
            rubric_assessments=[],
            assessment_modes={"Alice": "full", "Bob": "full"},
        )
        names = {s.candidate_name for s in summaries}
        assert "Alice" in names
        assert "Bob" in names

    def test_agent_highlights_populated(self) -> None:
        """Each candidate's highlights are built from that candidate's claim texts."""
        verdicts = {
            "role_fit": _verdict(
                "role_fit",
                [_claim("Alice", text="Alice shows strong technical depth in her portfolio.")],
                summary="Role fit agent summary text covering evaluation of Alice in detail.",
            ),
        }
        summaries = build_candidate_summaries(
            verdicts=verdicts,
            tension_map=[],
            rubric_assessments=[],
            assessment_modes={"Alice": "full"},
        )
        alice = next(s for s in summaries if s.candidate_name == "Alice")
        assert "role_fit" in alice.agent_highlights
        assert "Alice shows strong technical depth" in alice.agent_highlights["role_fit"]

    def test_agent_highlights_differ_per_candidate(self) -> None:
        """Highlights for Alice and Bob are different (per-candidate, not global)."""
        verdicts = {
            "role_fit": _verdict(
                "role_fit",
                [
                    _claim("Alice", text="Alice demonstrates exceptional enterprise architecture skills."),
                    _claim("Bob", text="Bob brings extensive M&A integration experience to the table."),
                ],
            ),
        }
        summaries = build_candidate_summaries(
            verdicts=verdicts,
            tension_map=[],
            rubric_assessments=[],
            assessment_modes={"Alice": "full", "Bob": "full"},
        )
        alice = next(s for s in summaries if s.candidate_name == "Alice")
        bob = next(s for s in summaries if s.candidate_name == "Bob")
        # Each candidate's highlight should reference only their own claim text
        assert "Alice" in alice.agent_highlights["role_fit"]
        assert "Bob" not in alice.agent_highlights["role_fit"]
        assert "Bob" in bob.agent_highlights["role_fit"]
        assert "Alice" not in bob.agent_highlights["role_fit"]

    def test_investigation_questions_from_rubric(self) -> None:
        """Investigation questions from rubric assessments are included."""
        rubric = [
            _assessment(
                "REQ-01",
                "Alice",
                RubricLevel.PARTIAL,
                investigation_question="What is Alice's experience with multi-BU programmes?",
            )
        ]
        verdicts = {"role_fit": _verdict("role_fit", [_claim("Alice")])}
        summaries = build_candidate_summaries(
            verdicts=verdicts,
            tension_map=[],
            rubric_assessments=rubric,
            assessment_modes={"Alice": "full"},
        )
        alice = next(s for s in summaries if s.candidate_name == "Alice")
        assert any("multi-BU" in q for q in alice.investigation_questions)

    def test_assessment_mode_reflected(self) -> None:
        """Assessment mode in summary matches the provided mode map."""
        verdicts = {"role_fit": _verdict("role_fit", [_claim("Alice")])}
        summaries = build_candidate_summaries(
            verdicts=verdicts,
            tension_map=[],
            rubric_assessments=[],
            assessment_modes={"Alice": "partial"},
        )
        alice = next(s for s in summaries if s.candidate_name == "Alice")
        assert alice.assessment_mode == "partial"


# ---------------------------------------------------------------------------
# Test 4: Contested signals — cross-agent disagreement detected
# ---------------------------------------------------------------------------


class TestContestedSignalsCrossAgent:
    """Cross-agent contested signal detection."""

    def test_cross_agent_disagreement_detected(self) -> None:
        """High-confidence and low-confidence citations of same reference → cross_agent contest."""
        verdicts = {
            "role_fit": _verdict(
                "role_fit",
                [_claim("Alice", ref="FLAG_X", confidence="high")],
            ),
            "risk": _verdict(
                "risk",
                [_claim("Alice", ref="FLAG_X", confidence="low")],
            ),
        }
        contested = detect_contested_signals(verdicts, tension_map=[])
        cross_agent = [c for c in contested if c.signal_type == "cross_agent"]
        assert len(cross_agent) >= 1
        assert cross_agent[0].candidate_name == "Alice"
        assert "role_fit" in cross_agent[0].agents_involved
        assert "risk" in cross_agent[0].agents_involved

    def test_no_contest_when_single_agent_cites_reference(self) -> None:
        """Only one agent citing a reference → no cross_agent contest (need at least 2 agents)."""
        verdicts = {
            "team_dynamics": _verdict("team_dynamics", [_claim("Alice", ref="FLAG_X", confidence="high")]),
        }
        contested = detect_contested_signals(verdicts, tension_map=[])
        cross_agent = [c for c in contested if c.signal_type == "cross_agent"]
        assert len(cross_agent) == 0

    def test_opposing_lens_roles_trigger_contest_regardless_of_confidence(self) -> None:
        """role_fit and risk citing same reference always constitutes an opposing-lens contest."""
        verdicts = {
            "role_fit": _verdict("role_fit", [_claim("Alice", ref="FLAG_X", confidence="high")]),
            "risk": _verdict("risk", [_claim("Alice", ref="FLAG_X", confidence="high")]),
        }
        contested = detect_contested_signals(verdicts, tension_map=[])
        cross_agent = [c for c in contested if c.signal_type == "cross_agent"]
        assert len(cross_agent) == 1
        assert cross_agent[0].candidate_name == "Alice"

    def test_contest_only_for_same_candidate(self) -> None:
        """Contest detection is per-candidate — different candidates don't trigger contest."""
        verdicts = {
            "role_fit": _verdict("role_fit", [_claim("Alice", ref="FLAG_X", confidence="high")]),
            "risk": _verdict("risk", [_claim("Bob", ref="FLAG_X", confidence="low")]),
        }
        contested = detect_contested_signals(verdicts, tension_map=[])
        cross_agent = [c for c in contested if c.signal_type == "cross_agent"]
        assert len(cross_agent) == 0


# ---------------------------------------------------------------------------
# Test 5: Contested signals — cross-stream tension detected
# ---------------------------------------------------------------------------


class TestContestedSignalsCrossStream:
    """Cross-stream contested signal detection."""

    def test_cross_stream_tension_detected(self) -> None:
        """A cross_stream TensionPair with a candidate who has verdict claims → cross_stream ContestedSignal."""
        tension = TensionPair(
            candidate_name="Alice",
            positive_flag="CV_EXCEEDS_REQ_01",
            negative_flag="EXECUTION_LOW_CONSCIENTIOUSNESS_RISK",
            domain="EXECUTION",
            tension_type="cross_stream",
            description="Strong CV evidence in EXECUTION alongside personality risk.",
        )
        verdicts = {
            "role_fit": _verdict("role_fit", [_claim("Alice")]),
            "risk": _verdict("risk", [_claim("Alice")]),
        }
        contested = detect_contested_signals(verdicts, tension_map=[tension])
        cross_stream = [c for c in contested if c.signal_type == "cross_stream"]
        assert len(cross_stream) == 1
        assert cross_stream[0].candidate_name == "Alice"
        assert cross_stream[0].signal_type == "cross_stream"

    def test_intra_stream_tension_not_surfaced_as_cross_stream(self) -> None:
        """Intra-stream TensionPairs are not surfaced as cross_stream ContestedSignals."""
        tension = TensionPair(
            candidate_name="Alice",
            positive_flag="FLAG_A",
            negative_flag="FLAG_B",
            domain="EXECUTION",
            tension_type="intra_stream",
            description="Conflicting signals within category.",
        )
        verdicts = {"role_fit": _verdict("role_fit", [_claim("Alice")])}
        contested = detect_contested_signals(verdicts, tension_map=[tension])
        cross_stream = [c for c in contested if c.signal_type == "cross_stream"]
        assert len(cross_stream) == 0


# ---------------------------------------------------------------------------
# Test 6: Provenance header — all fields from StageDOutput
# ---------------------------------------------------------------------------


class TestProvenanceHeader:
    """Provenance header correctly reflects StageDOutput fields."""

    def test_all_fields_populated(self) -> None:
        """Provenance header includes correct counts and modes."""
        reqs = [
            _req("REQ-01", assessable=True),
            _req("REQ-11", assessable=False),
        ]
        stage_d = _stage_d_output(
            candidates=["Alice", "Bob"],
            requirements=reqs,
        )
        header = build_provenance_header(stage_d, audit_warnings=[])
        assert header.requirement_count == 2
        assert header.cv_assessable_count == 1
        assert header.behavioral_count == 1
        assert header.candidate_count == 2
        assert "Alice" in header.assessment_modes
        assert "Bob" in header.assessment_modes
        assert header.quality_checks_passed is True

    def test_warnings_propagated(self) -> None:
        """Audit warnings appear in provenance header and quality_checks_passed is False."""
        stage_d = _stage_d_output()
        header = build_provenance_header(stage_d, audit_warnings=["Warning 1"])
        assert len(header.warnings) == 1
        assert header.quality_checks_passed is False

    def test_personality_sources_from_provenance(self) -> None:
        """Personality source per candidate is read from FlagProvenance."""
        stage_d = _stage_d_output(candidates=["Alice"])
        header = build_provenance_header(stage_d, audit_warnings=[])
        assert "Alice" in header.personality_sources
        assert header.personality_sources["Alice"] == "Big Five Manual"

    def test_flag_counts_from_provenance(self) -> None:
        """Flag counts per candidate are read from FlagProvenance.total_flags."""
        stage_d = _stage_d_output(candidates=["Alice"])
        header = build_provenance_header(stage_d, audit_warnings=[])
        assert "Alice" in header.flag_counts
        assert header.flag_counts["Alice"] == 5  # from _provenance default


# ---------------------------------------------------------------------------
# Test 7: Epistemic disclaimers — F10 always present, F09 only in partial mode
# ---------------------------------------------------------------------------


class TestEpistemicDisclaimers:
    """Disclaimer generation tests."""

    def test_f10_always_present(self) -> None:
        """F10 disclaimer is always returned regardless of mode."""
        disclaimer, _ = build_epistemic_disclaimers({"Alice": "full"})
        assert len(disclaimer) > 50
        assert "advisory" in disclaimer.lower() or "judgment" in disclaimer.lower()

    def test_f09_only_when_partial_mode_exists(self) -> None:
        """F09 partial disclaimer returned only when at least one candidate is partial."""
        _, partial_full = build_epistemic_disclaimers({"Alice": "full", "Bob": "full"})
        assert partial_full is None

        _, partial_mixed = build_epistemic_disclaimers({"Alice": "full", "Bob": "partial"})
        assert partial_mixed is not None
        assert "personality" in partial_mixed.lower()

    def test_f09_present_when_all_partial(self) -> None:
        """F09 disclaimer present when all candidates are partial mode."""
        _, partial_disclaimer = build_epistemic_disclaimers({"Alice": "partial"})
        assert partial_disclaimer is not None

    def test_f09_absent_when_no_candidates(self) -> None:
        """Empty mode map → no partial disclaimer."""
        _, partial_disclaimer = build_epistemic_disclaimers({})
        assert partial_disclaimer is None


# ---------------------------------------------------------------------------
# Test 8: Trade-off statement — mock LLM returns statement → included in output
# ---------------------------------------------------------------------------


class TestTradeOffStatement:
    """LLM call for trade-off statement."""

    @pytest.mark.asyncio
    async def test_statement_included_in_output(self) -> None:
        """Mock LLM response is returned as the trade-off statement."""
        expected = (
            "Alice excels on technical depth. Bob leads on industry experience. "
            "Both represent viable but distinct pathways."
        )
        client = _MockLLMClient(response=expected)
        matrix = [
            TradeOffCell(
                requirement_id="REQ-01",
                requirement_text="Tech leadership",
                active_priority="high",
                candidate_name="Alice",
                rubric_level="exceeds",
                confidence="high",
            )
        ]
        summaries = [
            CandidateSummary(
                candidate_name="Alice",
                assessment_mode="full",
                agent_highlights={"role_fit": "Alice is strong on technical delivery."},
                contested_signals=[],
                investigation_questions=[],
                unaddressed_flags=[],
            )
        ]
        result = await generate_trade_off_statement(matrix, summaries, client)
        assert result == expected

    @pytest.mark.asyncio
    async def test_statement_stripped_of_whitespace(self) -> None:
        """Trailing whitespace in LLM response is stripped."""
        client = _MockLLMClient(response="  Statement with spaces.  ")
        matrix: list[TradeOffCell] = []
        summaries: list[CandidateSummary] = []
        result = await generate_trade_off_statement(matrix, summaries, client)
        assert result == "Statement with spaces."

    @pytest.mark.asyncio
    async def test_fallback_returned_on_llm_error(self) -> None:
        """When the LLM call raises an exception, the fallback statement is returned."""
        from meridian.evaluation.synthesis.trade_off_statement import _FALLBACK_STATEMENT

        class _FailingLLMClient:
            async def complete(
                self,
                system: str,
                user: str,
                response_format: dict[str, Any] | None = None,
            ) -> str:
                raise RuntimeError("LLM unavailable")

        client = _FailingLLMClient()
        matrix: list[TradeOffCell] = []
        summaries: list[CandidateSummary] = []
        result = await generate_trade_off_statement(matrix, summaries, client)
        assert result == _FALLBACK_STATEMENT

    @pytest.mark.asyncio
    async def test_fallback_returned_on_empty_response(self) -> None:
        """When the LLM returns an empty string, the fallback statement is returned."""
        from meridian.evaluation.synthesis.trade_off_statement import _FALLBACK_STATEMENT

        client = _MockLLMClient(response="   ")
        matrix: list[TradeOffCell] = []
        summaries: list[CandidateSummary] = []
        result = await generate_trade_off_statement(matrix, summaries, client)
        assert result == _FALLBACK_STATEMENT


# ---------------------------------------------------------------------------
# Test 9: Full assembler — all sections present in SynthesisOutput
# ---------------------------------------------------------------------------


class TestFullAssembler:
    """Full assembler integration test."""

    @pytest.mark.asyncio
    async def test_all_sections_present(self) -> None:
        """Assembled SynthesisOutput contains all required sections."""
        stage_d = _stage_d_output(
            candidates=["Alice", "Bob"],
            requirements=[_req("REQ-01")],
            rubric_assessments=[
                _assessment("REQ-01", "Alice"),
                _assessment("REQ-01", "Bob"),
            ],
        )
        layer1 = _layer1_output()
        verdicts = {
            "role_fit": _verdict("role_fit", [_claim("Alice"), _claim("Bob")]),
        }
        client = _MockLLMClient()
        output = await assemble_synthesis(
            stage_d_output=stage_d,
            layer1_output=layer1,
            audited_verdicts=verdicts,
            audit_warnings=[],
            llm_client=client,
        )
        # All sections populated
        assert output.provenance is not None
        assert len(output.trade_off_matrix) > 0
        assert len(output.candidate_summaries) > 0
        assert len(output.trade_off_statement) > 0
        assert len(output.epistemic_disclaimer) > 0
        # Full mode → no partial disclaimer
        assert output.partial_mode_disclaimer is None

    @pytest.mark.asyncio
    async def test_partial_mode_disclaimer_present(self) -> None:
        """Partial mode candidate triggers F09 disclaimer in final output."""
        stage_d = _stage_d_output(
            candidates=["Alice"],
            requirements=[_req("REQ-01")],
            rubric_assessments=[_assessment("REQ-01", "Alice")],
            modes={"Alice": AssessmentMode.PARTIAL},
        )
        layer1 = _layer1_output()
        verdicts = {"role_fit": _verdict("role_fit", [_claim("Alice")])}
        client = _MockLLMClient()
        output = await assemble_synthesis(
            stage_d_output=stage_d,
            layer1_output=layer1,
            audited_verdicts=verdicts,
            audit_warnings=[],
            llm_client=client,
        )
        assert output.partial_mode_disclaimer is not None


# ---------------------------------------------------------------------------
# Test 10: Round-trip serialization
# ---------------------------------------------------------------------------


class TestRoundTrip:
    """SynthesisOutput round-trips through model_dump() / model_validate()."""

    @pytest.mark.asyncio
    async def test_round_trip_synthesis_output(self) -> None:
        """model_dump() → model_validate() reproduces identical SynthesisOutput."""
        stage_d = _stage_d_output(
            candidates=["Alice"],
            requirements=[_req("REQ-01")],
            rubric_assessments=[_assessment("REQ-01", "Alice")],
        )
        layer1 = _layer1_output()
        verdicts = {"role_fit": _verdict("role_fit", [_claim("Alice")])}
        client = _MockLLMClient()
        original = await assemble_synthesis(
            stage_d_output=stage_d,
            layer1_output=layer1,
            audited_verdicts=verdicts,
            audit_warnings=[],
            llm_client=client,
        )
        dumped = original.model_dump()
        restored = SynthesisOutput.model_validate(dumped)
        assert original == restored


# ---------------------------------------------------------------------------
# Test 11: Scenario switch — different scenario re-sorts rows
# ---------------------------------------------------------------------------


class TestScenarioSwitch:
    """Scenario switch changes row sort order but not rubric levels."""

    def test_row_sort_changes_with_scenario(self) -> None:
        """Same rubric assessments produce different row order under different scenarios."""
        reqs = [
            _req("REQ-01", dt_priority=Priority.HIGH, stab_priority=Priority.LOW),
            _req("REQ-02", dt_priority=Priority.LOW, stab_priority=Priority.HIGH),
        ]
        assessments = [
            _assessment("REQ-01", "Alice", RubricLevel.MEETS),
            _assessment("REQ-02", "Alice", RubricLevel.EXCEEDS),
        ]
        scenario_dt = _scenario(ScenarioName.DIGITAL_TRANSFORMATION)
        scenario_stab = _scenario(ScenarioName.STABILIZATION)

        matrix_dt = build_trade_off_matrix(
            rubric_assessments=assessments,
            requirements=reqs,
            scenario=scenario_dt,
            assessment_modes={"Alice": "full"},
        )
        matrix_stab = build_trade_off_matrix(
            rubric_assessments=assessments,
            requirements=reqs,
            scenario=scenario_stab,
            assessment_modes={"Alice": "full"},
        )
        # Under DT: REQ-01 (high) before REQ-02 (low)
        dt_order = [c.requirement_id for c in matrix_dt]
        assert dt_order.index("REQ-01") < dt_order.index("REQ-02")

        # Under stabilization: REQ-02 (high) before REQ-01 (low)
        stab_order = [c.requirement_id for c in matrix_stab]
        assert stab_order.index("REQ-02") < stab_order.index("REQ-01")

    def test_rubric_levels_unchanged_on_scenario_switch(self) -> None:
        """Rubric levels in cells are scenario-independent — only sort order changes."""
        reqs = [
            _req("REQ-01", dt_priority=Priority.HIGH, stab_priority=Priority.LOW),
            _req("REQ-02", dt_priority=Priority.LOW, stab_priority=Priority.HIGH),
        ]
        assessments = [
            _assessment("REQ-01", "Alice", RubricLevel.EXCEEDS),
            _assessment("REQ-02", "Alice", RubricLevel.GAP),
        ]
        matrix_dt = build_trade_off_matrix(
            rubric_assessments=assessments,
            requirements=reqs,
            scenario=_scenario(ScenarioName.DIGITAL_TRANSFORMATION),
            assessment_modes={"Alice": "full"},
        )
        matrix_stab = build_trade_off_matrix(
            rubric_assessments=assessments,
            requirements=reqs,
            scenario=_scenario(ScenarioName.STABILIZATION),
            assessment_modes={"Alice": "full"},
        )
        # Collect rubric levels by req_id for both scenarios
        levels_dt = {c.requirement_id: c.rubric_level for c in matrix_dt}
        levels_stab = {c.requirement_id: c.rubric_level for c in matrix_stab}

        assert levels_dt["REQ-01"] == "exceeds"
        assert levels_dt["REQ-02"] == "gap"
        # Same levels in both scenarios
        assert levels_dt == levels_stab
