"""Tests for E6: Self-Consistency Pre-Computation (Layer 3b).

Tests cover:
1. Deterministic mock → consistent (is_consistent=True, no annotations)
2. Varied mock → inconsistent (is_consistent=False, annotations present)
3. Ranking extraction from synthesis output
4. Ranking comparison — stable → no annotations
5. Ranking comparison — unstable → annotation with run_rankings
6. E1/E2 run once (not per-run)
7. num_runs=1 → always consistent
8. Run summaries collected from each run
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from meridian.evaluation.self_consistency import (
    ConsistencyResult,
    InstabilityAnnotation,
    _compare_rankings,
    _extract_candidate_ranking,
    run_consistency_check,
)
from meridian.evaluation.synthesis.models import (
    CandidateSummary,
    ProvenanceHeader,
    SynthesisOutput,
    TradeOffCell,
)
from meridian.models.candidates import BigFiveScores, CandidateData
from meridian.models.pipeline import AssessmentMode, FlagProvenance, StageDOutput
from meridian.models.requirements import Priority, Requirement, ScenarioPriority
from meridian.models.rubric import Confidence, RubricAssessment, RubricLevel
from meridian.models.scenarios import ScenarioConfig, ScenarioName

# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def _make_scenario_priority(default: Priority = Priority.MEDIUM) -> ScenarioPriority:
    return ScenarioPriority(
        digital_transformation=default,
        post_acquisition=default,
        turnaround=default,
        stabilization=default,
        growth=default,
    )


def _make_requirement(req_id: str = "REQ-01", text: str = "Some requirement") -> Requirement:
    return Requirement(
        requirement_id=req_id,
        text=text,
        source_quote=text,
        assessable_from_cv=True,
        scenario_priority=_make_scenario_priority(),
    )


def _make_rubric_assessment(
    req_id: str,
    candidate: str,
    level: RubricLevel = RubricLevel.MEETS,
) -> RubricAssessment:
    return RubricAssessment(
        requirement_id=req_id,
        candidate_name=candidate,
        rubric_level=level,
        confidence=Confidence.HIGH,
        cv_citation="Some CV citation",
    )


def _make_candidate(name: str, has_big_five: bool = True) -> CandidateData:
    big_five = BigFiveScores(O=0.7, C=0.8, E=0.6, A=0.7, N=0.3) if has_big_five else None
    return CandidateData(name=name, cv_text=f"CV text for {name}", big_five=big_five)


def _make_provenance(mode: AssessmentMode = AssessmentMode.FULL) -> FlagProvenance:
    return FlagProvenance(
        assessment_mode=mode,
        personality_flag_count=2,
        cv_flag_count=3,
        total_flags=5,
        big_five_available=(mode == AssessmentMode.FULL),
        personality_source="Big Five Manual",
        requirements_assessed=2,
        high_priority_gap_count=0,
    )


def _make_stage_d_output(
    candidates: list[str] | None = None,
) -> StageDOutput:
    candidates = candidates or ["Alice", "Bob"]
    reqs = [_make_requirement("REQ-01"), _make_requirement("REQ-02")]
    assessments = [_make_rubric_assessment("REQ-01", c) for c in candidates] + [
        _make_rubric_assessment("REQ-02", c) for c in candidates
    ]
    return StageDOutput(
        flags=[],
        provenance_per_candidate={c: _make_provenance() for c in candidates},
        confirmed_requirements=reqs,
        candidate_data=[_make_candidate(c) for c in candidates],
        rubric_matrix=assessments,
        scenario=ScenarioConfig(name=ScenarioName.DIGITAL_TRANSFORMATION, category_weights={}),
    )


def _make_trade_off_cell(
    req_id: str,
    candidate: str,
    rubric_level: str = "meets",
    priority: str = "high",
) -> TradeOffCell:
    return TradeOffCell(
        requirement_id=req_id,
        requirement_text=f"Requirement {req_id}",
        active_priority=priority,
        candidate_name=candidate,
        rubric_level=rubric_level,
        confidence="high",
        cv_citation=None,
    )


def _make_synthesis(
    candidates: list[str],
    rubric_levels: dict[str, str] | None = None,
    trade_off_statement: str = "Default trade-off statement.",
) -> SynthesisOutput:
    """Build a minimal SynthesisOutput for testing.

    rubric_levels: dict of candidate_name -> rubric_level (applies to REQ-01)
    """
    levels = rubric_levels or {c: "meets" for c in candidates}
    matrix = [_make_trade_off_cell("REQ-01", c, rubric_level=levels.get(c, "meets")) for c in candidates]
    summaries = [
        CandidateSummary(
            candidate_name=c,
            assessment_mode="full",
            agent_highlights={},
            contested_signals=[],
            investigation_questions=[],
            unaddressed_flags=[],
        )
        for c in candidates
    ]
    provenance = ProvenanceHeader(
        requirement_count=1,
        cv_assessable_count=1,
        behavioral_count=0,
        candidate_count=len(candidates),
        assessment_modes={c: "full" for c in candidates},
        personality_sources={c: "Big Five Manual" for c in candidates},
        flag_counts={c: 5 for c in candidates},
        quality_checks_passed=True,
        warnings=[],
    )
    return SynthesisOutput(
        provenance=provenance,
        trade_off_matrix=matrix,
        candidate_summaries=summaries,
        trade_off_statement=trade_off_statement,
        contested_signals=[],
        epistemic_disclaimer="This tool surfaces patterns.",
        partial_mode_disclaimer=None,
    )


def _make_valid_agent_verdict_json(role: str, candidate: str = "Alice") -> str:
    """Return valid agent JSON that can be parsed into AgentVerdict."""
    return json.dumps(
        {
            "agent_role": role,
            "claims": [
                {
                    "text": f"Claim about {candidate} based on available evidence for role assessment.",
                    "evidence_basis": {"type": "scored_flag", "reference": "EXECUTION_CONSCIENTIOUSNESS_FIT"},
                    "confidence": "high",
                    "candidate_name": candidate,
                }
            ],
            "summary": f"Summary for {role} agent covering all candidate assessments in this evaluation cycle.",
            "assessment_mode": "full",
            "unaddressed_flags": [],
        }
    )


# ---------------------------------------------------------------------------
# Test 1: Ranking extraction
# ---------------------------------------------------------------------------


class TestExtractCandidateRanking:
    """_extract_candidate_ranking tests."""

    def test_ranking_by_exceeds_count(self) -> None:
        """Candidate with more EXCEEDS ranks higher (lower rank number)."""
        synthesis = _make_synthesis(
            candidates=["Alice", "Bob"],
            rubric_levels={"Alice": "exceeds", "Bob": "meets"},
        )
        ranking = _extract_candidate_ranking(synthesis)
        assert ranking["Alice"] < ranking["Bob"]

    def test_ranking_by_gap_count_tiebreak(self) -> None:
        """With equal EXCEEDS, fewer GAPSs ranks higher."""
        # Build matrix with 2 requirements so we can differentiate gap counts.
        matrix = [
            _make_trade_off_cell("REQ-01", "Alice", "meets"),
            _make_trade_off_cell("REQ-02", "Alice", "gap"),  # 1 gap
            _make_trade_off_cell("REQ-01", "Bob", "meets"),
            _make_trade_off_cell("REQ-02", "Bob", "meets"),  # 0 gaps
        ]
        synthesis = _make_synthesis(["Alice", "Bob"])
        # Override matrix directly
        synthesis_with_matrix = SynthesisOutput(
            provenance=synthesis.provenance,
            trade_off_matrix=matrix,
            candidate_summaries=synthesis.candidate_summaries,
            trade_off_statement=synthesis.trade_off_statement,
            contested_signals=synthesis.contested_signals,
            epistemic_disclaimer=synthesis.epistemic_disclaimer,
        )
        ranking = _extract_candidate_ranking(synthesis_with_matrix)
        # Bob has 0 gaps, Alice has 1 gap — Bob ranks higher
        assert ranking["Bob"] < ranking["Alice"]

    def test_ranking_alphabetical_tiebreak(self) -> None:
        """With equal EXCEEDS and GAPS, alphabetical order applies."""
        synthesis = _make_synthesis(
            candidates=["Zoe", "Alice"],
            rubric_levels={"Zoe": "meets", "Alice": "meets"},
        )
        ranking = _extract_candidate_ranking(synthesis)
        # Alice comes before Zoe alphabetically → Alice rank 1
        assert ranking["Alice"] < ranking["Zoe"]

    def test_ranking_returns_1_indexed(self) -> None:
        """Rankings are 1-indexed."""
        synthesis = _make_synthesis(candidates=["Alice", "Bob"])
        ranking = _extract_candidate_ranking(synthesis)
        assert min(ranking.values()) == 1

    def test_single_candidate_ranked_first(self) -> None:
        """A single candidate is always ranked 1."""
        synthesis = _make_synthesis(candidates=["Alice"])
        ranking = _extract_candidate_ranking(synthesis)
        assert ranking["Alice"] == 1


# ---------------------------------------------------------------------------
# Test 2: Ranking comparison — stable
# ---------------------------------------------------------------------------


class TestCompareRankingsStable:
    """_compare_rankings tests where rankings are stable."""

    def test_identical_rankings_no_annotations(self) -> None:
        """Same ranking across all runs → empty annotation list."""
        rankings = [
            {"Alice": 1, "Bob": 2},
            {"Alice": 1, "Bob": 2},
            {"Alice": 1, "Bob": 2},
        ]
        annotations = _compare_rankings(rankings, ["Alice", "Bob"])
        assert annotations == []

    def test_single_run_always_consistent(self) -> None:
        """A single run can never produce instability."""
        rankings = [{"Alice": 1, "Bob": 2}]
        annotations = _compare_rankings(rankings, ["Alice", "Bob"])
        assert annotations == []

    def test_empty_candidate_list(self) -> None:
        """No candidates → no annotations."""
        annotations = _compare_rankings([{}, {}], [])
        assert annotations == []


# ---------------------------------------------------------------------------
# Test 3: Ranking comparison — unstable
# ---------------------------------------------------------------------------


class TestCompareRankingsUnstable:
    """_compare_rankings tests where rankings differ."""

    def test_instability_detected(self) -> None:
        """Different rankings across runs → annotation for changed candidate."""
        rankings = [
            {"Alice": 1, "Bob": 2},
            {"Alice": 2, "Bob": 1},  # Alice and Bob swap
            {"Alice": 1, "Bob": 2},
        ]
        annotations = _compare_rankings(rankings, ["Alice", "Bob"])
        annotated_names = {a.candidate_name for a in annotations}
        assert "Alice" in annotated_names
        assert "Bob" in annotated_names

    def test_run_rankings_captured_in_annotation(self) -> None:
        """InstabilityAnnotation captures per-run rankings."""
        rankings = [
            {"Alice": 1, "Bob": 2},
            {"Alice": 2, "Bob": 1},
        ]
        annotations = _compare_rankings(rankings, ["Alice", "Bob"])
        alice_ann = next(a for a in annotations if a.candidate_name == "Alice")
        assert alice_ann.run_rankings == (1, 2)

    def test_stable_candidate_not_annotated(self) -> None:
        """A candidate with consistent ranking is not annotated."""
        rankings = [
            {"Alice": 1, "Bob": 2, "Carol": 3},
            {"Alice": 2, "Bob": 1, "Carol": 3},  # Alice/Bob swap; Carol stable
        ]
        annotations = _compare_rankings(rankings, ["Alice", "Bob", "Carol"])
        annotated_names = {a.candidate_name for a in annotations}
        assert "Carol" not in annotated_names

    def test_annotation_description_contains_run_info(self) -> None:
        """Annotation description includes run ranking information."""
        rankings = [{"Alice": 1}, {"Alice": 2}]
        annotations = _compare_rankings(rankings, ["Alice"])
        assert len(annotations) == 1
        assert "run 1" in annotations[0].description
        assert "run 2" in annotations[0].description


# ---------------------------------------------------------------------------
# Test 4: Deterministic mock → consistent
# ---------------------------------------------------------------------------


class TestRunConsistencyCheckConsistent:
    """run_consistency_check with deterministic mock → always consistent."""

    def _make_mock_llm_client(self) -> Any:
        """Return a mock LLM client that always returns the same responses."""
        client = MagicMock()

        # Agent calls return role-specific JSON; synthesis call returns free text.
        async def _complete(
            system: str,
            user: str,
            response_format: dict[str, Any] | None = None,
        ) -> str:
            if response_format == {"type": "json_object"}:
                # Detect agent role from system prompt
                role = "role_fit"
                if "team dynamics" in system.lower() or "devil" in system.lower():
                    role = "team_dynamics"
                elif "risk" in system.lower():
                    role = "risk"
                # Build a verdict that mentions both candidates
                claims = [
                    {
                        "text": "Claim about Alice based on evidence for role assessment purposes.",
                        "evidence_basis": {
                            "type": "scored_flag",
                            "reference": "EXECUTION_CONSCIENTIOUSNESS_FIT",
                        },
                        "confidence": "high",
                        "candidate_name": "Alice",
                    },
                    {
                        "text": "Claim about Bob based on evidence for role assessment purposes.",
                        "evidence_basis": {
                            "type": "scored_flag",
                            "reference": "EXECUTION_CONSCIENTIOUSNESS_FIT",
                        },
                        "confidence": "high",
                        "candidate_name": "Bob",
                    },
                ]
                return json.dumps(
                    {
                        "agent_role": role,
                        "claims": claims,
                        "summary": (
                            f"Summary for {role} agent covering all candidate assessments in this evaluation cycle."
                        ),
                        "assessment_mode": "full",
                        "unaddressed_flags": [],
                    }
                )
            # Synthesis trade-off statement
            return "Alice excels in execution. Bob brings stronger strategic vision. Both merit committee deliberation."

        client.complete = _complete
        return client

    @pytest.mark.asyncio
    async def test_deterministic_mock_consistent(self) -> None:
        """Same mock responses every run → is_consistent=True, no annotations."""
        stage_d = _make_stage_d_output()
        client = self._make_mock_llm_client()

        # Patch assemble_synthesis to return deterministic synthesis with identical rankings.
        alice_exceeds = _make_synthesis(
            candidates=["Alice", "Bob"],
            rubric_levels={"Alice": "exceeds", "Bob": "meets"},
            trade_off_statement="Alice leads; Bob trails.",
        )

        with patch("meridian.evaluation.self_consistency.assemble_synthesis", return_value=alice_exceeds):
            result = await run_consistency_check(stage_d, client, num_runs=3)

        assert result.is_consistent is True
        assert result.annotations == ()
        assert result.num_runs == 3

    @pytest.mark.asyncio
    async def test_num_runs_parameter_used(self) -> None:
        """ConsistencyResult.num_runs reflects the requested num_runs."""
        stage_d = _make_stage_d_output()
        client = self._make_mock_llm_client()

        fixed_synthesis = _make_synthesis(["Alice", "Bob"])
        with patch("meridian.evaluation.self_consistency.assemble_synthesis", return_value=fixed_synthesis):
            result = await run_consistency_check(stage_d, client, num_runs=2)

        assert result.num_runs == 2


# ---------------------------------------------------------------------------
# Test 5: Varied mock → inconsistent
# ---------------------------------------------------------------------------


class TestRunConsistencyCheckInconsistent:
    """run_consistency_check with varying mock → detects instability."""

    @pytest.mark.asyncio
    async def test_varied_mock_inconsistent(self) -> None:
        """Different synthesis outputs per run → is_consistent=False, annotations present."""
        stage_d = _make_stage_d_output()
        client = MagicMock()

        # Synthesises with alternating rankings.
        alice_first = _make_synthesis(
            ["Alice", "Bob"],
            rubric_levels={"Alice": "exceeds", "Bob": "meets"},
            trade_off_statement="Run A statement.",
        )
        bob_first = _make_synthesis(
            ["Alice", "Bob"],
            rubric_levels={"Alice": "meets", "Bob": "exceeds"},
            trade_off_statement="Run B statement.",
        )
        alice_first_again = _make_synthesis(
            ["Alice", "Bob"],
            rubric_levels={"Alice": "exceeds", "Bob": "meets"},
            trade_off_statement="Run C statement.",
        )

        syntheses = [alice_first, bob_first, alice_first_again]
        call_count = [0]

        async def _patched_assemble(*args: Any, **kwargs: Any) -> SynthesisOutput:
            idx = call_count[0]
            call_count[0] += 1
            return syntheses[idx % len(syntheses)]

        with patch("meridian.evaluation.self_consistency.assemble_synthesis", side_effect=_patched_assemble):
            # run_agents and run_audit still need mocking
            client.complete = AsyncMock(return_value="trade-off text")
            with (
                patch("meridian.evaluation.self_consistency.run_agents", return_value={}),
                patch(
                    "meridian.evaluation.self_consistency.run_audit",
                    return_value=({}, []),
                ),
            ):
                result = await run_consistency_check(stage_d, client, num_runs=3)

        assert result.is_consistent is False
        assert len(result.annotations) > 0

    @pytest.mark.asyncio
    async def test_annotations_contain_candidate_names(self) -> None:
        """Annotations reference the unstable candidates by name."""
        stage_d = _make_stage_d_output()
        client = MagicMock()
        client.complete = AsyncMock(return_value="trade-off")

        alice_first = _make_synthesis(
            ["Alice", "Bob"],
            rubric_levels={"Alice": "exceeds", "Bob": "meets"},
        )
        bob_first = _make_synthesis(
            ["Alice", "Bob"],
            rubric_levels={"Alice": "meets", "Bob": "exceeds"},
        )
        syntheses = [alice_first, bob_first]
        call_count = [0]

        async def _patched(*args: Any, **kwargs: Any) -> SynthesisOutput:
            idx = call_count[0]
            call_count[0] += 1
            return syntheses[idx % len(syntheses)]

        with (
            patch("meridian.evaluation.self_consistency.assemble_synthesis", side_effect=_patched),
            patch("meridian.evaluation.self_consistency.run_agents", return_value={}),
            patch("meridian.evaluation.self_consistency.run_audit", return_value=({}, [])),
        ):
            result = await run_consistency_check(stage_d, client, num_runs=2)

        annotated_names = {a.candidate_name for a in result.annotations}
        assert "Alice" in annotated_names or "Bob" in annotated_names


# ---------------------------------------------------------------------------
# Test 6: E1/E2 run exactly once
# ---------------------------------------------------------------------------


class TestE1E2RunOnce:
    """Verify E1 (validation) and E2 (signals) are called exactly once."""

    @pytest.mark.asyncio
    async def test_e1_e2_run_once_not_per_run(self) -> None:
        """validate_stage_d_output and compute_layer1 are called once regardless of num_runs."""
        stage_d = _make_stage_d_output()
        client = MagicMock()
        client.complete = AsyncMock(return_value="trade-off")

        fixed_synthesis = _make_synthesis(["Alice", "Bob"])

        with (
            patch("meridian.evaluation.self_consistency.validate_stage_d_output", wraps=lambda x: (x, [])) as mock_e1,
            patch(
                "meridian.evaluation.self_consistency.compute_layer1",
                wraps=lambda flags, scenario, candidate_names, assessment_modes: MagicMock(
                    tension_map=[],
                    signal_labels={},
                    risk_bands={},
                    weighted_scores_per_candidate={},
                    partial_mode_notes=[],
                ),
            ) as mock_e2,
            patch("meridian.evaluation.self_consistency.assemble_synthesis", return_value=fixed_synthesis),
            patch("meridian.evaluation.self_consistency.run_agents", return_value={}),
            patch("meridian.evaluation.self_consistency.run_audit", return_value=({}, [])),
        ):
            await run_consistency_check(stage_d, client, num_runs=3)

        # E1 and E2 each called exactly once.
        assert mock_e1.call_count == 1
        assert mock_e2.call_count == 1


# ---------------------------------------------------------------------------
# Test 7: num_runs=1 always consistent
# ---------------------------------------------------------------------------


class TestNumRunsOne:
    """num_runs=1 is always consistent by definition."""

    @pytest.mark.asyncio
    async def test_num_runs_zero_raises(self) -> None:
        """num_runs=0 raises ValueError immediately."""
        stage_d = _make_stage_d_output()
        client = MagicMock()

        with pytest.raises(ValueError, match="num_runs must be >= 1"):
            await run_consistency_check(stage_d, client, num_runs=0)

    @pytest.mark.asyncio
    async def test_num_runs_negative_raises(self) -> None:
        """Negative num_runs raises ValueError immediately."""
        stage_d = _make_stage_d_output()
        client = MagicMock()

        with pytest.raises(ValueError, match="num_runs must be >= 1"):
            await run_consistency_check(stage_d, client, num_runs=-1)

    @pytest.mark.asyncio
    async def test_single_run_always_consistent(self) -> None:
        """A single run produces no instability annotations."""
        stage_d = _make_stage_d_output()
        client = MagicMock()
        client.complete = AsyncMock(return_value="trade-off")

        any_synthesis = _make_synthesis(["Alice", "Bob"])
        with (
            patch("meridian.evaluation.self_consistency.assemble_synthesis", return_value=any_synthesis),
            patch("meridian.evaluation.self_consistency.run_agents", return_value={}),
            patch("meridian.evaluation.self_consistency.run_audit", return_value=({}, [])),
        ):
            result = await run_consistency_check(stage_d, client, num_runs=1)

        assert result.is_consistent is True
        assert result.annotations == ()
        assert result.num_runs == 1


# ---------------------------------------------------------------------------
# Test 8: Run summaries collected
# ---------------------------------------------------------------------------


class TestRunSummariesCollected:
    """Trade-off statements are captured from each run."""

    @pytest.mark.asyncio
    async def test_run_summaries_collected(self) -> None:
        """Each run's trade-off statement is captured in run_summaries."""
        stage_d = _make_stage_d_output()
        client = MagicMock()
        client.complete = AsyncMock(return_value="trade-off")

        summaries_by_run = ["First run statement.", "Second run statement.", "Third run statement."]
        call_count = [0]

        async def _patched_assemble(*args: Any, **kwargs: Any) -> SynthesisOutput:
            idx = call_count[0]
            call_count[0] += 1
            return _make_synthesis(
                ["Alice", "Bob"],
                trade_off_statement=summaries_by_run[idx],
            )

        with (
            patch("meridian.evaluation.self_consistency.assemble_synthesis", side_effect=_patched_assemble),
            patch("meridian.evaluation.self_consistency.run_agents", return_value={}),
            patch("meridian.evaluation.self_consistency.run_audit", return_value=({}, [])),
        ):
            result = await run_consistency_check(stage_d, client, num_runs=3)

        assert result.run_summaries == tuple(summaries_by_run)

    @pytest.mark.asyncio
    async def test_run_summaries_count_matches_num_runs(self) -> None:
        """Number of run_summaries equals num_runs."""
        stage_d = _make_stage_d_output()
        client = MagicMock()
        client.complete = AsyncMock(return_value="trade-off")

        fixed = _make_synthesis(["Alice", "Bob"], trade_off_statement="Statement.")
        with (
            patch("meridian.evaluation.self_consistency.assemble_synthesis", return_value=fixed),
            patch("meridian.evaluation.self_consistency.run_agents", return_value={}),
            patch("meridian.evaluation.self_consistency.run_audit", return_value=({}, [])),
        ):
            result = await run_consistency_check(stage_d, client, num_runs=2)

        assert len(result.run_summaries) == 2


# ---------------------------------------------------------------------------
# Test 9: Frozen dataclass immutability
# ---------------------------------------------------------------------------


class TestFrozenDataclasses:
    """InstabilityAnnotation and ConsistencyResult are frozen (immutable)."""

    def test_instability_annotation_is_frozen(self) -> None:
        """Attempting to mutate InstabilityAnnotation raises FrozenInstanceError."""
        ann = InstabilityAnnotation(
            candidate_name="Alice",
            description="Test",
            run_rankings=(1, 2),
        )
        with pytest.raises((AttributeError, TypeError)):
            ann.candidate_name = "Bob"  # type: ignore[misc]

    def test_consistency_result_is_frozen(self) -> None:
        """Attempting to mutate ConsistencyResult raises FrozenInstanceError."""
        result = ConsistencyResult(
            num_runs=2,
            is_consistent=True,
            annotations=(),
            run_summaries=("A", "B"),
        )
        with pytest.raises((AttributeError, TypeError)):
            result.is_consistent = False  # type: ignore[misc]
