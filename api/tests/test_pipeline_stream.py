"""Tests for Pipeline SSE Stream (A4).

Covers:
1. Full stream yields all expected event types in order
2. C3 events arrive per-candidate (one C3_CANDIDATE_DONE per candidate)
3. E3 events arrive per-agent (one AGENT_COMPLETE or AGENT_TIMEOUT per agent)
4. Error mid-pipeline yields ERROR event and stream terminates
5. All event data payloads are JSON-serializable
6. Scenario switch stream yields correct subset of events (no C1/C3 events)
7. _convert_candidate_input correctly maps CandidateInput → CandidateData
8. _resolve_scenario resolves known names and raises on unknown
9. Events appear in the correct positional order
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from shared.models import (
    CandidateData,
    Requirement,
    RubricLevel,
    ScenarioConfig,
    ScenarioName,
)

from api.jobs.models import CandidateInput
from api.sse.events import SSEEvent, SSEEventType
from api.sse.pipeline_stream import (
    _assessment_stats,
    _convert_candidate_input,
    _count_cv_flags,
    _count_not_assessable,
    _count_personality_flags,
    _resolve_scenario,
    evaluate_pipeline_stream,
    switch_scenario_stream,
)
from api.tests._pipeline_fixtures import (
    build_cached_state,
    build_full_pipeline_llm_client,
    build_mock_requirements,
    build_mock_rubric_assessments,
    build_switch_llm_client,
    collect,
    make_candidate,
    make_cv_flag,
    make_personality_flag,
    make_requirement,
    make_rubric_assessment,
    make_scenario,
    make_stage_d_output,
)

# ---------------------------------------------------------------------------
# Backward-compatible local aliases used by unit tests below
# ---------------------------------------------------------------------------

_make_scenario = make_scenario
_make_requirement = make_requirement
_make_candidate = make_candidate
_make_rubric_assessment = make_rubric_assessment
_make_cv_flag = make_cv_flag
_make_personality_flag = make_personality_flag
_make_stage_d_output = make_stage_d_output
_collect = collect
_build_mock_requirements = build_mock_requirements
_build_mock_rubric_assessments = build_mock_rubric_assessments


# ---------------------------------------------------------------------------
# Unit tests: helper functions
# ---------------------------------------------------------------------------


class TestConvertCandidateInput:
    """_convert_candidate_input maps CandidateInput fields to CandidateData correctly."""

    def test_minimal_candidate_no_big_five(self) -> None:
        inputs = [CandidateInput(name="Alice", cv_text="Alice CV text")]
        result = _convert_candidate_input(inputs)
        assert len(result) == 1
        assert result[0].name == "Alice"
        assert result[0].cv_text == "Alice CV text"
        assert result[0].big_five is None

    def test_candidate_with_big_five(self) -> None:
        inputs = [
            CandidateInput(
                name="Bob",
                cv_text="Bob CV text",
                big_five={"O": 0.7, "C": 0.8, "E": 0.6, "A": 0.5, "N": 0.3},
                personality_source="manual",
            )
        ]
        result = _convert_candidate_input(inputs)
        assert result[0].big_five is not None
        assert pytest.approx(0.7) == result[0].big_five.O
        assert result[0].personality_source == "manual"

    def test_multiple_candidates(self) -> None:
        inputs = [CandidateInput(name=f"Candidate {i}", cv_text=f"CV {i}") for i in range(3)]
        result = _convert_candidate_input(inputs)
        assert len(result) == 3
        assert [c.name for c in result] == ["Candidate 0", "Candidate 1", "Candidate 2"]


class TestResolveScenario:
    """_resolve_scenario maps name strings to ScenarioConfig objects."""

    def test_valid_scenario_names(self) -> None:
        for name in ScenarioName:
            config = _resolve_scenario(name.value)
            assert config.name == name
            assert isinstance(config.category_weights, dict)

    def test_case_insensitive(self) -> None:
        config = _resolve_scenario("DIGITAL_TRANSFORMATION")
        assert config.name == ScenarioName.DIGITAL_TRANSFORMATION

    def test_unknown_scenario_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown scenario"):
            _resolve_scenario("not_a_real_scenario")


class TestAssessmentStats:
    """_assessment_stats counts rubric levels correctly."""

    def test_empty_list(self) -> None:
        stats = _assessment_stats([])
        assert stats == {"exceeds": 0, "meets": 0, "partial": 0, "gap": 0, "not_assessable": 0}

    def test_mixed_levels(self) -> None:
        assessments = [
            _make_rubric_assessment("R1", "Alice", RubricLevel.EXCEEDS),
            _make_rubric_assessment("R2", "Alice", RubricLevel.MEETS),
            _make_rubric_assessment("R3", "Alice", RubricLevel.GAP),
            _make_rubric_assessment("R4", "Alice", RubricLevel.PARTIAL),
            _make_rubric_assessment("R5", "Alice", RubricLevel.NOT_ASSESSABLE),
        ]
        stats = _assessment_stats(assessments)
        assert stats["exceeds"] == 1
        assert stats["meets"] == 1
        assert stats["gap"] == 1
        assert stats["partial"] == 1
        assert stats["not_assessable"] == 1


class TestFlagCountHelpers:
    """_count_personality_flags and _count_cv_flags work correctly."""

    def test_personality_flag_count(self) -> None:
        flags = [
            _make_personality_flag("Alice"),
            _make_cv_flag("R1", "Alice"),
        ]
        assert _count_personality_flags(flags) == 1
        assert _count_cv_flags(flags) == 1

    def test_empty_flag_list(self) -> None:
        assert _count_personality_flags([]) == 0
        assert _count_cv_flags([]) == 0


class TestCountNotAssessable:
    """_count_not_assessable counts NOT_ASSESSABLE rubric levels correctly."""

    def test_no_not_assessable(self) -> None:
        assessments = [_make_rubric_assessment("R1", "Alice", RubricLevel.MEETS)]
        assert _count_not_assessable(assessments) == 0

    def test_counts_not_assessable(self) -> None:
        assessments = [
            _make_rubric_assessment("R1", "Alice", RubricLevel.NOT_ASSESSABLE),
            _make_rubric_assessment("R2", "Alice", RubricLevel.NOT_ASSESSABLE),
            _make_rubric_assessment("R3", "Alice", RubricLevel.MEETS),
        ]
        assert _count_not_assessable(assessments) == 2


# ---------------------------------------------------------------------------
# Full pipeline stream tests
# ---------------------------------------------------------------------------


class TestEvaluatePipelineStream:
    """evaluate_pipeline_stream yields events in order with correct types."""

    @pytest.fixture()
    def candidates(self) -> list[CandidateData]:
        return [
            _make_candidate("Alice"),
            _make_candidate("Bob"),
            _make_candidate("Carol"),
        ]

    @pytest.fixture()
    def scenario(self) -> ScenarioConfig:
        return _make_scenario()

    @pytest.fixture()
    def requirements(self) -> list[Requirement]:
        return _build_mock_requirements(count=2)

    def _make_llm_client(self, requirements: list[Requirement], candidates: list[CandidateData]) -> Any:
        """Build a MockLLMClient with responses for all pipeline LLM calls."""
        return build_full_pipeline_llm_client(requirements, candidates)

    async def test_full_stream_yields_all_expected_event_types(
        self,
        candidates: list[CandidateData],
        scenario: ScenarioConfig,
        requirements: list[Requirement],
    ) -> None:
        """Full pipeline stream must include all major checkpoint events."""
        llm_client = self._make_llm_client(requirements, candidates)

        events = await _collect(
            evaluate_pipeline_stream(
                jd_text="Chief Technology Officer required.",
                candidates=candidates,
                scenario=scenario,
                llm_client=llm_client,
                job_id="test-job-1",
            )
        )
        event_types = [e.event for e in events]

        required = [
            SSEEventType.JOB_CREATED,
            SSEEventType.C1_STARTED,
            SSEEventType.C1_COMPLETE,
            SSEEventType.C2_COMPLETE,
            SSEEventType.C3_STARTED,
            SSEEventType.C4_COMPLETE,
            SSEEventType.STAGE_D_COMPLETE,
            SSEEventType.SIGNALS_COMPUTED,
            SSEEventType.AGENTS_STARTED,
            SSEEventType.AUDIT_COMPLETE,
            SSEEventType.SYNTHESIS_STARTED,
            SSEEventType.SYNTHESIS_COMPLETE,
            SSEEventType.COMPLETE,
        ]
        for event_type in required:
            assert event_type in event_types, f"Missing event type: {event_type}"

    async def test_c3_candidate_done_events_per_candidate(
        self,
        candidates: list[CandidateData],
        scenario: ScenarioConfig,
        requirements: list[Requirement],
    ) -> None:
        """Must yield exactly one C3_CANDIDATE_DONE event per candidate."""
        llm_client = self._make_llm_client(requirements, candidates)

        events = await _collect(
            evaluate_pipeline_stream(
                jd_text="CTO required.",
                candidates=candidates,
                scenario=scenario,
                llm_client=llm_client,
                job_id="test-job-2",
            )
        )
        c3_done_events = [e for e in events if e.event == SSEEventType.C3_CANDIDATE_DONE]
        assert len(c3_done_events) == len(candidates), (
            f"Expected {len(candidates)} C3_CANDIDATE_DONE events, got {len(c3_done_events)}"
        )

        # Verify all candidate names appear
        candidate_names_seen = {e.data["candidate"] for e in c3_done_events}
        candidate_names_expected = {c.name for c in candidates}
        assert candidate_names_seen == candidate_names_expected

    async def test_c3_candidate_done_counters_increment(
        self,
        candidates: list[CandidateData],
        scenario: ScenarioConfig,
        requirements: list[Requirement],
    ) -> None:
        """C3_CANDIDATE_DONE events must carry ascending done/total counters."""
        llm_client = self._make_llm_client(requirements, candidates)

        events = await _collect(
            evaluate_pipeline_stream(
                jd_text="CTO required.",
                candidates=candidates,
                scenario=scenario,
                llm_client=llm_client,
                job_id="test-job-3",
            )
        )
        c3_done_events = [e for e in events if e.event == SSEEventType.C3_CANDIDATE_DONE]
        done_values = sorted(e.data["done"] for e in c3_done_events)
        assert done_values == list(range(1, len(candidates) + 1))

        for e in c3_done_events:
            assert e.data["total"] == len(candidates)

    async def test_agent_events_per_agent(
        self,
        candidates: list[CandidateData],
        scenario: ScenarioConfig,
        requirements: list[Requirement],
    ) -> None:
        """Must yield exactly 3 AGENT_COMPLETE or AGENT_TIMEOUT events."""
        llm_client = self._make_llm_client(requirements, candidates)

        events = await _collect(
            evaluate_pipeline_stream(
                jd_text="CTO required.",
                candidates=candidates,
                scenario=scenario,
                llm_client=llm_client,
                job_id="test-job-4",
            )
        )
        agent_events = [e for e in events if e.event in {SSEEventType.AGENT_COMPLETE, SSEEventType.AGENT_TIMEOUT}]
        assert len(agent_events) == 3, f"Expected 3 agent events, got {len(agent_events)}"

    async def test_agent_names_are_all_three_roles(
        self,
        candidates: list[CandidateData],
        scenario: ScenarioConfig,
        requirements: list[Requirement],
    ) -> None:
        """Agent events must cover all three expected agent roles."""
        llm_client = self._make_llm_client(requirements, candidates)

        events = await _collect(
            evaluate_pipeline_stream(
                jd_text="CTO required.",
                candidates=candidates,
                scenario=scenario,
                llm_client=llm_client,
                job_id="test-job-5",
            )
        )
        agent_events = [e for e in events if e.event in {SSEEventType.AGENT_COMPLETE, SSEEventType.AGENT_TIMEOUT}]
        agent_names = {e.data["agent_name"] for e in agent_events}
        assert agent_names == {"role_fit", "team_dynamics", "risk"}

    async def test_all_event_data_payloads_are_json_serializable(
        self,
        candidates: list[CandidateData],
        scenario: ScenarioConfig,
        requirements: list[Requirement],
    ) -> None:
        """Every event's data payload must survive json.dumps/json.loads round-trip."""
        llm_client = self._make_llm_client(requirements, candidates)

        events = await _collect(
            evaluate_pipeline_stream(
                jd_text="CTO required.",
                candidates=candidates,
                scenario=scenario,
                llm_client=llm_client,
                job_id="test-job-6",
            )
        )
        for event in events:
            serialized = json.dumps(event.data)
            recovered = json.loads(serialized)
            assert isinstance(recovered, dict), f"Event {event.event} data is not a dict"

    async def test_no_cv_text_in_event_payloads(
        self,
        candidates: list[CandidateData],
        scenario: ScenarioConfig,
        requirements: list[Requirement],
    ) -> None:
        """No event payload should contain raw CV text."""
        llm_client = self._make_llm_client(requirements, candidates)

        events = await _collect(
            evaluate_pipeline_stream(
                jd_text="CTO required.",
                candidates=candidates,
                scenario=scenario,
                llm_client=llm_client,
                job_id="test-job-7",
            )
        )
        for event in events:
            serialized = json.dumps(event.data)
            for candidate in candidates:
                # cv_text is a distinctive prefix not found in legitimate rubric payloads
                assert f"CV text for {candidate.name}" not in serialized, f"CV text leaked in event {event.event}"

    async def test_job_created_carries_correct_job_id(
        self,
        candidates: list[CandidateData],
        scenario: ScenarioConfig,
        requirements: list[Requirement],
    ) -> None:
        """JOB_CREATED event must carry the correct job_id."""
        llm_client = self._make_llm_client(requirements, candidates)

        events = await _collect(
            evaluate_pipeline_stream(
                jd_text="CTO required.",
                candidates=candidates,
                scenario=scenario,
                llm_client=llm_client,
                job_id="my-specific-job-id",
            )
        )
        job_created = next(e for e in events if e.event == SSEEventType.JOB_CREATED)
        assert job_created.data["job_id"] == "my-specific-job-id"
        assert job_created.data["candidate_count"] == len(candidates)
        assert job_created.data["scenario"] == scenario.name.value

    async def test_complete_event_is_last(
        self,
        candidates: list[CandidateData],
        scenario: ScenarioConfig,
        requirements: list[Requirement],
    ) -> None:
        """COMPLETE event must be the final event when pipeline succeeds."""
        llm_client = self._make_llm_client(requirements, candidates)

        events = await _collect(
            evaluate_pipeline_stream(
                jd_text="CTO required.",
                candidates=candidates,
                scenario=scenario,
                llm_client=llm_client,
                job_id="test-job-8",
            )
        )
        assert events[-1].event == SSEEventType.COMPLETE

    async def test_error_mid_pipeline_yields_error_event(
        self,
        candidates: list[CandidateData],
        scenario: ScenarioConfig,
    ) -> None:
        """When an exception occurs, stream yields ERROR event and terminates."""

        # The client raises an error on the first call (C1 extraction will fail to parse)
        class _FailingClient:
            async def complete(self, system: str, user: str, response_format: Any = None) -> str:
                raise RuntimeError("LLM backend unavailable")

        events = await _collect(
            evaluate_pipeline_stream(
                jd_text="CTO required.",
                candidates=candidates,
                scenario=scenario,
                llm_client=_FailingClient(),  # type: ignore[arg-type]
                job_id="failing-job",
            )
        )

        # Should yield JOB_CREATED then ERROR
        event_types = [e.event for e in events]
        assert SSEEventType.ERROR in event_types, "Expected ERROR event in stream"

        # ERROR event must be terminal (last event)
        assert events[-1].event == SSEEventType.ERROR

        error_event = events[-1]
        assert "LLM backend unavailable" in error_event.data["message"]
        assert error_event.data["job_id"] == "failing-job"

    async def test_error_event_does_not_contain_stack_trace(
        self,
        candidates: list[CandidateData],
        scenario: ScenarioConfig,
    ) -> None:
        """Error message must be capped at 500 chars (no huge stack traces)."""

        class _FailingClient:
            async def complete(self, system: str, user: str, response_format: Any = None) -> str:
                raise ValueError("x" * 1000)

        events = await _collect(
            evaluate_pipeline_stream(
                jd_text="CTO required.",
                candidates=candidates,
                scenario=scenario,
                llm_client=_FailingClient(),  # type: ignore[arg-type]
                job_id="long-error-job",
            )
        )
        error_event = next(e for e in events if e.event == SSEEventType.ERROR)
        assert len(error_event.data["message"]) <= 500

    async def test_event_ordering(
        self,
        candidates: list[CandidateData],
        scenario: ScenarioConfig,
        requirements: list[Requirement],
    ) -> None:
        """Events must appear in the correct positional order through the pipeline."""
        llm_client = self._make_llm_client(requirements, candidates)

        events = await _collect(
            evaluate_pipeline_stream(
                jd_text="CTO required.",
                candidates=candidates,
                scenario=scenario,
                llm_client=llm_client,
                job_id="ordering-test-job",
            )
        )
        types = [e.event for e in events]

        assert types.index(SSEEventType.C1_COMPLETE) < types.index(SSEEventType.C3_STARTED)
        assert types.index(SSEEventType.C3_STARTED) < types.index(SSEEventType.STAGE_D_COMPLETE)
        assert types.index(SSEEventType.STAGE_D_COMPLETE) < types.index(SSEEventType.AGENTS_STARTED)
        assert types.index(SSEEventType.AGENTS_STARTED) < types.index(SSEEventType.SYNTHESIS_COMPLETE)
        assert types.index(SSEEventType.SYNTHESIS_COMPLETE) < types.index(SSEEventType.COMPLETE)


# ---------------------------------------------------------------------------
# Scenario switch stream tests
# ---------------------------------------------------------------------------


class TestSwitchScenarioStream:
    """switch_scenario_stream yields correct event subset — no C1/C3."""

    @pytest.fixture()
    def candidates(self) -> list[CandidateData]:
        return [
            _make_candidate("Alice"),
            _make_candidate("Bob"),
        ]

    @pytest.fixture()
    def requirements(self) -> list[Requirement]:
        return _build_mock_requirements(count=2)

    def _make_cached_state(
        self,
        candidates: list[CandidateData],
        requirements: list[Requirement],
    ) -> Any:
        """Build a CachedPipelineState from pre-built data."""
        return build_cached_state(candidates, requirements)

    def _make_llm_client(
        self,
        candidates: list[CandidateData],
        requirements: list[Requirement],
    ) -> Any:
        """Build a MockLLMClient for scenario switch (no C1/C3 calls)."""
        return build_switch_llm_client(requirements, candidates)

    async def test_switch_stream_has_no_c1_or_c3_events(
        self,
        candidates: list[CandidateData],
        requirements: list[Requirement],
    ) -> None:
        """Scenario switch must not emit C1 or C3 events (they use cached data)."""
        cached = self._make_cached_state(candidates, requirements)
        llm_client = self._make_llm_client(candidates, requirements)
        new_scenario = _make_scenario(ScenarioName.TURNAROUND)

        events = await _collect(
            switch_scenario_stream(
                cached_state=cached,
                new_scenario=new_scenario,
                llm_client=llm_client,
                job_id="switch-job-1",
                from_scenario="digital_transformation",
            )
        )
        event_types = {e.event for e in events}

        # C1 and C3 events must not appear
        c1_c3_types = {
            SSEEventType.C1_STARTED,
            SSEEventType.C1_COMPLETE,
            SSEEventType.C2_COMPLETE,
            SSEEventType.C3_STARTED,
            SSEEventType.C3_CANDIDATE_DONE,
            SSEEventType.C4_COMPLETE,
        }
        assert event_types.isdisjoint(c1_c3_types), (
            f"Unexpected C1/C3 events in switch stream: {event_types & c1_c3_types}"
        )

    async def test_switch_stream_starts_with_switch_started(
        self,
        candidates: list[CandidateData],
        requirements: list[Requirement],
    ) -> None:
        """First event must be SWITCH_STARTED."""
        cached = self._make_cached_state(candidates, requirements)
        llm_client = self._make_llm_client(candidates, requirements)
        new_scenario = _make_scenario(ScenarioName.GROWTH)

        events = await _collect(
            switch_scenario_stream(
                cached_state=cached,
                new_scenario=new_scenario,
                llm_client=llm_client,
                job_id="switch-job-2",
                from_scenario="digital_transformation",
            )
        )
        assert events[0].event == SSEEventType.SWITCH_STARTED
        assert events[0].data["to_scenario"] == "growth"
        assert events[0].data["from_scenario"] == "digital_transformation"
        assert events[0].data["job_id"] == "switch-job-2"

    async def test_switch_stream_ends_with_switch_complete(
        self,
        candidates: list[CandidateData],
        requirements: list[Requirement],
    ) -> None:
        """Last event in a successful switch must be SWITCH_COMPLETE."""
        cached = self._make_cached_state(candidates, requirements)
        llm_client = self._make_llm_client(candidates, requirements)
        new_scenario = _make_scenario(ScenarioName.GROWTH)

        events = await _collect(
            switch_scenario_stream(
                cached_state=cached,
                new_scenario=new_scenario,
                llm_client=llm_client,
                job_id="switch-job-3",
                from_scenario="digital_transformation",
            )
        )
        assert events[-1].event == SSEEventType.SWITCH_COMPLETE
        switch_complete = events[-1]
        assert switch_complete.data["new_scenario"] == "growth"
        assert switch_complete.data["reused_rubric_cells"] == len(cached.rubric_assessments)

    async def test_switch_stream_has_three_agent_events(
        self,
        candidates: list[CandidateData],
        requirements: list[Requirement],
    ) -> None:
        """Switch stream must also emit 3 agent events (E3 still runs)."""
        cached = self._make_cached_state(candidates, requirements)
        llm_client = self._make_llm_client(candidates, requirements)
        new_scenario = _make_scenario(ScenarioName.TURNAROUND)

        events = await _collect(
            switch_scenario_stream(
                cached_state=cached,
                new_scenario=new_scenario,
                llm_client=llm_client,
                job_id="switch-job-4",
                from_scenario="digital_transformation",
            )
        )
        agent_events = [e for e in events if e.event in {SSEEventType.AGENT_COMPLETE, SSEEventType.AGENT_TIMEOUT}]
        assert len(agent_events) == 3

    async def test_switch_stream_error_yields_error_event(
        self,
        candidates: list[CandidateData],
        requirements: list[Requirement],
    ) -> None:
        """When an exception occurs in switch stream, ERROR event is emitted.

        We patch run_stage_d to raise so the error propagates before any agent
        calls happen (agents silently degrade; Stage D failure is unrecoverable).
        """
        import stage_d.pipeline as stage_d_pipeline
        from stage_e.scenario_switch import CachedPipelineState

        rubric_assessments = _build_mock_rubric_assessments(candidates, requirements)
        cached = CachedPipelineState(
            requirements=requirements,
            rubric_assessments=rubric_assessments,
            candidates=candidates,
            extraction_warnings=[],
        )

        original_run_stage_d = stage_d_pipeline.run_stage_d

        def _failing_run_stage_d(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("Stage D failure in switch")

        stage_d_pipeline.run_stage_d = _failing_run_stage_d  # type: ignore[assignment]
        try:
            from shared.llm_client import MockLLMClient

            llm_client = MockLLMClient("irrelevant")
            new_scenario = _make_scenario(ScenarioName.STABILIZATION)
            events = await _collect(
                switch_scenario_stream(
                    cached_state=cached,
                    new_scenario=new_scenario,
                    llm_client=llm_client,
                    job_id="failing-switch",
                    from_scenario="digital_transformation",
                )
            )
        finally:
            stage_d_pipeline.run_stage_d = original_run_stage_d  # type: ignore[assignment]

        event_types = [e.event for e in events]
        assert SSEEventType.ERROR in event_types
        assert events[-1].event == SSEEventType.ERROR
        error_event = events[-1]
        assert error_event.data["code"] == "SWITCH_ERROR"
        assert "Stage D failure in switch" in error_event.data["message"]

    async def test_switch_stream_all_payloads_json_serializable(
        self,
        candidates: list[CandidateData],
        requirements: list[Requirement],
    ) -> None:
        """Every event payload in the switch stream must be JSON-serializable."""
        cached = self._make_cached_state(candidates, requirements)
        llm_client = self._make_llm_client(candidates, requirements)
        new_scenario = _make_scenario(ScenarioName.GROWTH)

        events = await _collect(
            switch_scenario_stream(
                cached_state=cached,
                new_scenario=new_scenario,
                llm_client=llm_client,
                job_id="switch-json-test",
                from_scenario="digital_transformation",
            )
        )
        for event in events:
            serialized = json.dumps(event.data)
            recovered = json.loads(serialized)
            assert isinstance(recovered, dict)


# ---------------------------------------------------------------------------
# SSEEvent wrapper integrity
# ---------------------------------------------------------------------------


class TestSSEEventWrapper:
    """All events from the pipeline generators are valid SSEEvent objects."""

    async def test_events_are_sse_event_instances(self) -> None:
        """Every item yielded must be an SSEEvent."""
        from shared.llm_client import MockLLMClient

        requirements = _build_mock_requirements(count=1)
        candidates = [_make_candidate("Solo")]
        scenario = _make_scenario()

        c1_response = json.dumps(
            {
                "requirements": [
                    {
                        "requirement_id": requirements[0].requirement_id,
                        "text": requirements[0].text,
                        "source_quote": requirements[0].source_quote,
                        "assessable_from_cv": True,
                        "scenario_priority": {
                            "digital_transformation": "high",
                            "post_acquisition": "medium",
                            "turnaround": "medium",
                            "stabilization": "low",
                            "growth": "medium",
                        },
                    }
                ]
            }
        )
        c3_response = json.dumps(
            [
                {
                    "requirement_id": requirements[0].requirement_id,
                    "candidate_name": "Solo",
                    "rubric_level": "meets",
                    "confidence": "high",
                    "cv_citation": "Evidence from CV",
                }
            ]
        )
        agent_response = json.dumps(
            {
                "agent_role": "role_fit",
                "claims": [
                    {
                        "text": "Solo shows strong signals",
                        "evidence_basis": {"type": "cv_rubric", "reference": requirements[0].requirement_id},
                        "confidence": "high",
                        "candidate_name": "Solo",
                    }
                ],
                "summary": "Solo is a strong candidate.",
                "assessment_mode": "full",
                "unaddressed_flags": [],
            }
        )
        synthesis_response = json.dumps({"trade_off_statement": "Solo is well-suited."})

        responses = [c1_response, c3_response, agent_response, agent_response, agent_response, synthesis_response]
        llm_client = MockLLMClient(responses)

        events = await _collect(
            evaluate_pipeline_stream(
                jd_text="CEO required.",
                candidates=candidates,
                scenario=scenario,
                llm_client=llm_client,
                job_id="wrapper-test",
            )
        )
        for event in events:
            assert isinstance(event, SSEEvent)
            assert isinstance(event.event, SSEEventType)
            assert isinstance(event.data, dict)
