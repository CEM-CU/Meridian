"""Tests for SSE event schema and stream helpers (A3).

Covers:
- SSEEventType enum completeness (20 values)
- Each payload model validates correctly and rejects extra fields
- format_sse_event produces correct EventSource wire format
- SSEEvent.data is JSON-serialisable
- sse_response_generator yields correct formatted strings
- sse_response_generator emits an error event when the source raises
"""

import json
import typing
from collections.abc import AsyncIterator

import pytest

from api.sse.events import (
    PAYLOAD_MODELS,
    AgentCompletePayload,
    AgentsStartedPayload,
    AgentTimeoutPayload,
    AuditCompletePayload,
    C1CompletePayload,
    C1StartedPayload,
    C2CompletePayload,
    C3CandidateDonePayload,
    C3StartedPayload,
    C4CompletePayload,
    CompletePayload,
    ErrorPayload,
    JobCreatedPayload,
    SignalsComputedPayload,
    SSEEvent,
    SSEEventType,
    StageDCompletePayload,
    SwitchCompletePayload,
    SwitchStartedPayload,
    SynthesisCompletePayload,
    SynthesisStartedPayload,
)
from api.sse.stream import format_sse_event, sse_response_generator

# ---------------------------------------------------------------------------
# SSEEventType enum completeness
# ---------------------------------------------------------------------------


class TestSSEEventType:
    """SSEEventType must contain all 20 pipeline checkpoints."""

    EXPECTED_VALUES: typing.ClassVar[set[str]] = {
        "job_created",
        "c1_started",
        "c1_complete",
        "c2_complete",
        "c3_started",
        "c3_candidate_done",
        "c4_complete",
        "stage_d_complete",
        "signals_computed",
        "agents_started",
        "agent_complete",
        "agent_timeout",
        "audit_complete",
        "synthesis_started",
        "synthesis_complete",
        "switch_started",
        "switch_complete",
        "complete",
        "error",
    }

    def test_minimum_value_count(self) -> None:
        """Enum must have at least 19 members (the spec minimum)."""
        assert len(SSEEventType) >= 19

    def test_all_expected_values_present(self) -> None:
        """Every expected event value must be a member of SSEEventType."""
        actual = {e.value for e in SSEEventType}
        missing = self.EXPECTED_VALUES - actual
        assert not missing, f"Missing SSEEventType values: {missing}"

    def test_is_str_enum(self) -> None:
        """SSEEventType values must be plain strings (StrEnum)."""
        assert isinstance(SSEEventType.JOB_CREATED, str)
        assert SSEEventType.JOB_CREATED == "job_created"

    def test_payload_models_covers_all_event_types(self) -> None:
        """PAYLOAD_MODELS must have an entry for every SSEEventType."""
        missing = set(SSEEventType) - set(PAYLOAD_MODELS.keys())
        assert not missing, f"PAYLOAD_MODELS missing entries for: {missing}"


# ---------------------------------------------------------------------------
# Payload model validation — happy path
# ---------------------------------------------------------------------------


class TestPayloadModels:
    """Each payload model validates correct data and rejects extras."""

    def test_job_created_payload(self) -> None:
        p = JobCreatedPayload(
            job_id="j1",
            scenario="digital_transformation",
            candidate_count=3,
            created_at="2026-03-29T00:00:00Z",
        )
        assert p.job_id == "j1"
        assert p.candidate_count == 3

    def test_c1_started_payload(self) -> None:
        p = C1StartedPayload(job_id="j1")
        assert p.job_id == "j1"

    def test_c1_complete_payload(self) -> None:
        p = C1CompletePayload(
            requirements=[{"id": "r1", "text": "Python"}],
            cv_assessable=1,
            behavioral=0,
            warnings=[],
        )
        assert p.cv_assessable == 1
        assert isinstance(p.requirements, list)

    def test_c2_complete_payload(self) -> None:
        p = C2CompletePayload(scenario="turnaround", requirement_count=12)
        assert p.scenario == "turnaround"

    def test_c3_started_payload(self) -> None:
        p = C3StartedPayload(candidate_count=3, requirement_count=12)
        assert p.candidate_count == 3

    def test_c3_candidate_done_payload(self) -> None:
        p = C3CandidateDonePayload(
            candidate="Marcus",
            cells=[{"req_id": "r1", "level": "meets"}],
            stats={"exceeds": 2, "meets": 5, "partial": 3, "gap": 1, "not_assessable": 1},
            done=1,
            total=3,
        )
        assert p.candidate == "Marcus"
        assert p.stats["meets"] == 5

    def test_c4_complete_payload(self) -> None:
        p = C4CompletePayload(cv_flag_count=8, drop_count=2)
        assert p.cv_flag_count == 8

    def test_stage_d_complete_payload(self) -> None:
        p = StageDCompletePayload(
            flag_count=20,
            personality_flag_count=12,
            cv_flag_count=8,
            validation_warnings=[],
            assessment_modes={"Marcus": "full", "Sarah": "partial"},
            per_candidate={
                "Marcus": {
                    "mode": "full", "personality_flags": 8, "cv_flags": 4,
                    "total": 12, "big_five_available": True,
                },
                "Sarah": {
                    "mode": "partial", "personality_flags": 0, "cv_flags": 4,
                    "total": 4, "big_five_available": False,
                },
            },
        )
        assert p.flag_count == 20
        assert p.assessment_modes["Marcus"] == "full"
        assert p.per_candidate["Marcus"]["mode"] == "full"

    def test_signals_computed_payload(self) -> None:
        p = SignalsComputedPayload(
            signal_count=15,
            tension_pairs=3,
            scenario="growth",
            signal_labels={"Marcus": "positive", "Sarah": "mixed"},
            risk_bands={"Marcus": "low", "Sarah": "moderate"},
            tensions=[],
            partial_mode_notes=[],
        )
        assert p.tension_pairs == 3
        assert p.signal_labels["Marcus"] == "positive"
        assert p.risk_bands["Sarah"] == "moderate"

    def test_agents_started_payload(self) -> None:
        p = AgentsStartedPayload(agent_names=["execution", "strategic", "cultural"])
        assert len(p.agent_names) == 3

    def test_agent_complete_payload(self) -> None:
        p = AgentCompletePayload(
            agent_name="execution",
            finding_count=5,
            evidence_count=12,
            elapsed_seconds=4.2,
            summary="Strong signals observed across execution domain.",
            evidence_types={"cv_rubric": 8, "scored_flag": 4},
            unaddressed_flags=["DARK_SIDE_FLAG"],
        )
        assert p.agent_name == "execution"
        assert p.elapsed_seconds == pytest.approx(4.2)
        assert p.summary == "Strong signals observed across execution domain."
        assert p.evidence_types["cv_rubric"] == 8
        assert p.unaddressed_flags == ["DARK_SIDE_FLAG"]

    def test_agent_timeout_payload(self) -> None:
        p = AgentTimeoutPayload(agent_name="strategic", timeout_seconds=30.0)
        assert p.timeout_seconds == pytest.approx(30.0)

    def test_audit_complete_payload(self) -> None:
        p = AuditCompletePayload(
            checks_run=8,
            checks_passed=7,
            checks_failed=1,
            audit_warnings=["F05 semantic drift detected"],
        )
        assert p.checks_failed == 1

    def test_synthesis_started_payload(self) -> None:
        p = SynthesisStartedPayload(candidate_count=3)
        assert p.candidate_count == 3

    def test_synthesis_complete_payload(self) -> None:
        p = SynthesisCompletePayload(
            candidates={"Marcus": "strong_hire", "Sarah": "hire"},
            trade_off_count=4,
            investigation_question_count=6,
            trade_off_matrix=[{"requirement_id": "R1", "candidate_name": "Marcus", "rubric_level": "exceeds"}],
            candidate_summaries=[{"candidate_name": "Marcus", "assessment_mode": "full"}],
            trade_off_statement="Marcus is the strongest overall candidate.",
            contested_signals=[],
            provenance={"requirement_count": 5, "candidate_count": 2},
            epistemic_disclaimer="This is a data-driven assessment.",
            partial_mode_disclaimer=None,
        )
        assert p.candidates["Marcus"] == "strong_hire"
        assert p.trade_off_statement == "Marcus is the strongest overall candidate."
        assert p.epistemic_disclaimer == "This is a data-driven assessment."
        assert p.partial_mode_disclaimer is None

    def test_switch_started_payload(self) -> None:
        p = SwitchStartedPayload(
            job_id="j1",
            from_scenario="digital_transformation",
            to_scenario="turnaround",
        )
        assert p.to_scenario == "turnaround"

    def test_switch_complete_payload(self) -> None:
        p = SwitchCompletePayload(job_id="j1", new_scenario="turnaround", reused_rubric_cells=30)
        assert p.reused_rubric_cells == 30

    def test_complete_payload(self) -> None:
        p = CompletePayload(job_id="j1", elapsed_seconds=42.5, result_summary="3 candidates evaluated")
        assert p.elapsed_seconds == pytest.approx(42.5)

    def test_error_payload_with_stage(self) -> None:
        p = ErrorPayload(job_id="j1", code="C1_FAILED", message="LLM refused request", stage="stage_c")
        assert p.stage == "stage_c"

    def test_error_payload_without_job_id(self) -> None:
        p = ErrorPayload(job_id=None, code="UNKNOWN", message="Unexpected error")
        assert p.job_id is None

    # --- extra="forbid" enforcement ---

    def test_c1_complete_rejects_extra_fields(self) -> None:
        """extra='forbid' means unknown fields raise ValidationError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            C1CompletePayload(
                requirements=[],
                cv_assessable=0,
                behavioral=0,
                warnings=[],
                unexpected_field="boom",  # type: ignore[call-arg]
            )

    def test_agent_complete_rejects_extra_fields(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AgentCompletePayload(
                agent_name="execution",
                finding_count=1,
                evidence_count=2,
                elapsed_seconds=1.0,
                bonus="oops",  # type: ignore[call-arg]
            )


# ---------------------------------------------------------------------------
# SSEEvent wrapper
# ---------------------------------------------------------------------------


class TestSSEEvent:
    """SSEEvent wrapper validation and JSON-serialisability."""

    def test_sse_event_holds_event_type_and_data(self) -> None:
        event = SSEEvent(
            event=SSEEventType.JOB_CREATED,
            data={"job_id": "j1", "scenario": "growth", "candidate_count": 2, "created_at": "2026-01-01T00:00:00Z"},
        )
        assert event.event == SSEEventType.JOB_CREATED
        assert event.data["job_id"] == "j1"

    def test_sse_event_data_is_json_serialisable(self) -> None:
        """data dict must round-trip through json.dumps / json.loads."""
        event = SSEEvent(
            event=SSEEventType.C1_COMPLETE,
            data=C1CompletePayload(
                requirements=[{"id": "r1", "text": "Python"}],
                cv_assessable=1,
                behavioral=0,
                warnings=["low confidence"],
            ).model_dump(),
        )
        serialised = json.dumps(event.data)
        recovered = json.loads(serialised)
        assert recovered["cv_assessable"] == 1

    def test_sse_event_rejects_extra_fields(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SSEEvent(
                event=SSEEventType.COMPLETE,
                data={},
                extra_attr="no",  # type: ignore[call-arg]
            )


# ---------------------------------------------------------------------------
# format_sse_event wire format
# ---------------------------------------------------------------------------


class TestFormatSSEEvent:
    """format_sse_event must produce valid EventSource wire format."""

    def _make_event(self) -> SSEEvent:
        return SSEEvent(
            event=SSEEventType.JOB_CREATED,
            data={"job_id": "j42", "scenario": "growth", "candidate_count": 1, "created_at": "2026-01-01T00:00:00Z"},
        )

    def test_starts_with_event_line(self) -> None:
        wire = format_sse_event(self._make_event())
        assert wire.startswith("event: job_created\n")

    def test_contains_data_line(self) -> None:
        wire = format_sse_event(self._make_event())
        assert "\ndata: " in wire

    def test_ends_with_double_newline(self) -> None:
        """EventSource spec requires \\n\\n to terminate each event."""
        wire = format_sse_event(self._make_event())
        assert wire.endswith("\n\n")

    def test_data_line_is_valid_json(self) -> None:
        wire = format_sse_event(self._make_event())
        lines = wire.strip().splitlines()
        # line 0: "event: ...", line 1: "data: ..."
        data_line = lines[1]
        assert data_line.startswith("data: ")
        payload_json = data_line[len("data: ") :]
        parsed = json.loads(payload_json)
        assert parsed["job_id"] == "j42"

    def test_exact_structure(self) -> None:
        """Wire string must have exactly two non-empty lines + trailing newlines."""
        wire = format_sse_event(self._make_event())
        # Split on single newline; last two chars are \\n\\n
        assert wire.count("\n") == 3  # event\\ndata\\n\\n → 3 newlines

    def test_error_event_wire_format(self) -> None:
        event = SSEEvent(
            event=SSEEventType.ERROR,
            data=ErrorPayload(job_id=None, code="BOOM", message="Something broke").model_dump(),
        )
        wire = format_sse_event(event)
        assert wire.startswith("event: error\n")
        assert wire.endswith("\n\n")


# ---------------------------------------------------------------------------
# sse_response_generator
# ---------------------------------------------------------------------------


async def _events_from_list(items: list[SSEEvent]) -> AsyncIterator[SSEEvent]:
    """Helper: yield SSEEvents from a plain list."""
    for item in items:
        yield item


async def _raising_iterator(exc: Exception) -> AsyncIterator[SSEEvent]:
    """Helper: yield one event then raise."""
    yield SSEEvent(
        event=SSEEventType.C1_STARTED,
        data=C1StartedPayload(job_id="j1").model_dump(),
    )
    raise exc


class TestSSEResponseGenerator:
    """sse_response_generator must yield correct wire format strings."""

    @pytest.mark.asyncio
    async def test_yields_formatted_strings(self) -> None:
        events = [
            SSEEvent(
                event=SSEEventType.JOB_CREATED,
                data=JobCreatedPayload(
                    job_id="j1",
                    scenario="growth",
                    candidate_count=2,
                    created_at="2026-01-01T00:00:00Z",
                ).model_dump(),
            ),
            SSEEvent(
                event=SSEEventType.COMPLETE,
                data=CompletePayload(
                    job_id="j1",
                    elapsed_seconds=10.0,
                    result_summary="done",
                ).model_dump(),
            ),
        ]
        chunks: list[str] = []
        async for chunk in sse_response_generator(_events_from_list(events)):
            chunks.append(chunk)

        assert len(chunks) == 2
        assert chunks[0].startswith("event: job_created\n")
        assert chunks[1].startswith("event: complete\n")
        for chunk in chunks:
            assert chunk.endswith("\n\n")

    @pytest.mark.asyncio
    async def test_yields_error_event_on_exception(self) -> None:
        """When the source raises, generator must emit an ERROR event and stop."""
        exc = RuntimeError("pipeline exploded")
        chunks: list[str] = []
        async for chunk in sse_response_generator(_raising_iterator(exc)):
            chunks.append(chunk)

        # First chunk is the normally-yielded c1_started event
        assert chunks[0].startswith("event: c1_started\n")
        # Last chunk must be the error event
        last = chunks[-1]
        assert "event: error\n" in last
        assert "pipeline exploded" in last

    @pytest.mark.asyncio
    async def test_empty_iterator_yields_nothing(self) -> None:
        """An empty source iterator must produce no output."""

        async def _empty() -> AsyncIterator[SSEEvent]:
            return
            yield  # make it an async generator

        chunks: list[str] = []
        async for chunk in sse_response_generator(_empty()):
            chunks.append(chunk)
        assert chunks == []

    @pytest.mark.asyncio
    async def test_data_in_yielded_chunks_is_valid_json(self) -> None:
        """Every data line in the output must carry valid JSON."""
        events = [
            SSEEvent(
                event=SSEEventType.STAGE_D_COMPLETE,
                data=StageDCompletePayload(
                    flag_count=10,
                    personality_flag_count=6,
                    cv_flag_count=4,
                    validation_warnings=["W1"],
                    assessment_modes={"Alice": "full"},
                    per_candidate={
                        "Alice": {
                            "mode": "full", "personality_flags": 3, "cv_flags": 3,
                            "total": 6, "big_five_available": True,
                        },
                    },
                ).model_dump(),
            )
        ]
        async for chunk in sse_response_generator(_events_from_list(events)):
            lines = chunk.strip().splitlines()
            data_line = next(line for line in lines if line.startswith("data: "))
            payload = json.loads(data_line[len("data: ") :])
            assert payload["flag_count"] == 10
