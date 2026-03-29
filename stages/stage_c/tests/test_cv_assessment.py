"""Tests for C3: CV rubric assessment — core parsing, citation enforcement,
single-candidate assessment, parallel orchestration, and property tests.

Prompt builder tests live in test_cv_assessment_prompt.py.
Drop detection tests live in test_cv_assessment_drops.py.
All tests use MockLLMClient — no real API calls.
"""

from __future__ import annotations

import json

import pytest
from _helpers import (
    MockLLMClient,
    make_assessment_dict,
    make_candidate,
    make_requirement,
    make_rubric_assessment,
    make_scenario,
    make_scenario_priority,
)
from hypothesis import given, settings
from hypothesis import strategies as st
from shared.models import (
    Confidence,
    Priority,
    RubricAssessment,
    RubricLevel,
    ScenarioName,
)
from stage_c.cv_assessment import (
    _build_priority_order,
    assess_all_candidates,
    assess_candidate,
    enforce_citations,
    parse_assessment_response,
)

# ---------------------------------------------------------------------------
# parse_assessment_response tests
# ---------------------------------------------------------------------------


class TestParseAssessmentResponse:
    """Tests for parse_assessment_response."""

    def test_valid_json_returns_assessments(self) -> None:
        """Valid JSON array → correct RubricAssessment list."""
        data = [
            make_assessment_dict("REQ-01", "Alice", "meets", "high"),
            make_assessment_dict("REQ-02", "Alice", "gap", "high", None, None, None, "Why no EV experience?"),
        ]
        raw = json.dumps(data)
        result = parse_assessment_response(raw, "Alice", ["REQ-01", "REQ-02"])
        assert len(result) == 2
        assert result[0].requirement_id == "REQ-01"
        assert result[0].rubric_level == RubricLevel.MEETS
        assert result[1].requirement_id == "REQ-02"
        assert result[1].rubric_level == RubricLevel.GAP

    def test_markdown_fences_stripped(self) -> None:
        """Response wrapped in ```json ... ``` is parsed correctly."""
        data = [make_assessment_dict()]
        raw = f"```json\n{json.dumps(data)}\n```"
        result = parse_assessment_response(raw, "Alice", ["REQ-01"])
        assert len(result) == 1
        assert result[0].rubric_level == RubricLevel.MEETS

    def test_plain_fences_stripped(self) -> None:
        """Response wrapped in plain ``` ... ``` is parsed correctly."""
        data = [make_assessment_dict()]
        raw = f"```\n{json.dumps(data)}\n```"
        result = parse_assessment_response(raw, "Alice", ["REQ-01"])
        assert len(result) == 1

    def test_invalid_json_raises_value_error(self) -> None:
        """Non-JSON response raises ValueError."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_assessment_response("not json at all", "Alice", ["REQ-01"])

    def test_non_array_json_raises_value_error(self) -> None:
        """JSON object (not array) raises ValueError."""
        with pytest.raises(ValueError, match="Expected JSON array"):
            parse_assessment_response('{"requirement_id": "REQ-01"}', "Alice", ["REQ-01"])

    def test_candidate_name_injected_when_missing(self) -> None:
        """If LLM omits candidate_name, it is injected from the parameter."""
        data = [
            {
                "requirement_id": "REQ-01",
                "candidate_name": "",  # blank
                "rubric_level": "meets",
                "confidence": "high",
                "cv_citation": "Led 300-person org",
                "cv_location": "CTO role",
                "notes": None,
                "investigation_question": None,
            }
        ]
        raw = json.dumps(data)
        result = parse_assessment_response(raw, "Bob", ["REQ-01"])
        assert result[0].candidate_name == "Bob"

    def test_candidate_name_preserved_when_present(self) -> None:
        """If LLM provides a candidate_name, it is preserved."""
        data = [make_assessment_dict("REQ-01", "Alice")]
        raw = json.dumps(data)
        result = parse_assessment_response(raw, "Alice", ["REQ-01"])
        assert result[0].candidate_name == "Alice"

    def test_schema_validation_error_raises_value_error(self) -> None:
        """Assessment with invalid rubric_level raises ValueError."""
        data = [
            {
                "requirement_id": "REQ-01",
                "candidate_name": "Alice",
                "rubric_level": "spectacular",  # invalid
                "confidence": "high",
                "cv_citation": None,
                "cv_location": None,
                "notes": None,
                "investigation_question": None,
            }
        ]
        with pytest.raises(ValueError):
            parse_assessment_response(json.dumps(data), "Alice", ["REQ-01"])

    def test_all_rubric_levels_accepted(self) -> None:
        """All 5 rubric levels parse without error."""
        for level in ("exceeds", "meets", "partial", "gap", "not_assessable"):
            citation = "Some evidence" if level in ("exceeds", "meets", "partial") else None
            location = "CTO role" if level in ("exceeds", "meets", "partial") else None
            data = [make_assessment_dict("REQ-01", "Alice", level, "high", citation, location)]
            result = parse_assessment_response(json.dumps(data), "Alice", ["REQ-01"])
            assert result[0].rubric_level == RubricLevel(level)


# ---------------------------------------------------------------------------
# enforce_citations tests
# ---------------------------------------------------------------------------


class TestEnforceCitations:
    """Tests for enforce_citations."""

    def test_meets_with_citation_unchanged(self) -> None:
        """MEETS with a citation is not modified."""
        a = make_rubric_assessment(level=RubricLevel.MEETS, cv_citation="Some passage")
        corrected, warnings = enforce_citations([a])
        assert len(warnings) == 0
        assert corrected[0].rubric_level == RubricLevel.MEETS
        assert corrected[0].cv_citation == "Some passage"

    def test_exceeds_with_citation_unchanged(self) -> None:
        """EXCEEDS with a citation is not modified."""
        a = make_rubric_assessment(level=RubricLevel.EXCEEDS, cv_citation="USD 1.2B P&L")
        corrected, warnings = enforce_citations([a])
        assert len(warnings) == 0
        assert corrected[0].rubric_level == RubricLevel.EXCEEDS

    def test_partial_with_citation_unchanged(self) -> None:
        """PARTIAL with a citation is not modified."""
        a = make_rubric_assessment(level=RubricLevel.PARTIAL, cv_citation="Some partial evidence")
        corrected, warnings = enforce_citations([a])
        assert len(warnings) == 0
        assert corrected[0].rubric_level == RubricLevel.PARTIAL

    def test_meets_without_citation_downgraded_to_gap(self) -> None:
        """MEETS without cv_citation is downgraded to GAP."""
        a = make_rubric_assessment(level=RubricLevel.MEETS, cv_citation=None, cv_location=None)
        corrected, warnings = enforce_citations([a])
        assert len(warnings) == 1
        assert "CITATION_MISSING" in warnings[0]
        assert corrected[0].rubric_level == RubricLevel.GAP

    def test_exceeds_without_citation_downgraded_to_gap(self) -> None:
        """EXCEEDS without cv_citation is downgraded to GAP."""
        a = make_rubric_assessment(level=RubricLevel.EXCEEDS, cv_citation=None, cv_location=None)
        corrected, warnings = enforce_citations([a])
        assert corrected[0].rubric_level == RubricLevel.GAP
        assert "CITATION_MISSING" in warnings[0]

    def test_partial_without_citation_downgraded_to_gap(self) -> None:
        """PARTIAL without cv_citation is downgraded to GAP."""
        a = make_rubric_assessment(level=RubricLevel.PARTIAL, cv_citation=None, cv_location=None)
        corrected, _warnings = enforce_citations([a])
        assert corrected[0].rubric_level == RubricLevel.GAP

    def test_gap_without_citation_unchanged(self) -> None:
        """GAP without citation is not modified (GAP never needs a citation)."""
        a = make_rubric_assessment(
            level=RubricLevel.GAP,
            cv_citation=None,
            cv_location=None,
        )
        corrected, warnings = enforce_citations([a])
        assert len(warnings) == 0
        assert corrected[0].rubric_level == RubricLevel.GAP

    def test_not_assessable_without_citation_unchanged(self) -> None:
        """NOT_ASSESSABLE without citation is not modified."""
        a = make_rubric_assessment(level=RubricLevel.NOT_ASSESSABLE, cv_citation=None, cv_location=None)
        corrected, warnings = enforce_citations([a])
        assert len(warnings) == 0
        assert corrected[0].rubric_level == RubricLevel.NOT_ASSESSABLE

    def test_downgrade_adds_citation_missing_to_notes(self) -> None:
        """Downgraded assessment has CITATION_MISSING appended to notes."""
        a = make_rubric_assessment(level=RubricLevel.MEETS, cv_citation=None, cv_location=None)
        corrected, _ = enforce_citations([a])
        assert corrected[0].notes is not None
        assert "CITATION_MISSING" in corrected[0].notes

    def test_downgrade_preserves_existing_notes(self) -> None:
        """Downgraded assessment preserves any prior notes text."""
        a = RubricAssessment(
            requirement_id="REQ-01",
            candidate_name="Alice",
            rubric_level=RubricLevel.MEETS,
            confidence=Confidence.HIGH,
            cv_citation=None,
            notes="Recency concern from 2018 role",
        )
        corrected, _ = enforce_citations([a])
        notes = corrected[0].notes or ""
        assert "Recency concern from 2018 role" in notes
        assert "CITATION_MISSING" in notes

    def test_input_list_not_mutated(self) -> None:
        """enforce_citations returns a new list; the input list is unchanged."""
        a = make_rubric_assessment(level=RubricLevel.MEETS, cv_citation=None, cv_location=None)
        original_level = a.rubric_level
        enforce_citations([a])
        assert a.rubric_level == original_level  # original unchanged

    def test_empty_string_citation_treated_as_missing(self) -> None:
        """MEETS with cv_citation="" (empty string) is downgraded like None."""
        a = make_rubric_assessment(level=RubricLevel.MEETS, cv_citation="", cv_location="")
        corrected, warnings = enforce_citations([a])
        assert corrected[0].rubric_level == RubricLevel.GAP
        assert len(warnings) == 1
        assert "CITATION_MISSING" in warnings[0]

    def test_mixed_assessments_only_violators_downgraded(self) -> None:
        """Only assessments missing citations are downgraded; others pass through."""
        good = make_rubric_assessment("REQ-01", level=RubricLevel.MEETS, cv_citation="Evidence A")
        bad = make_rubric_assessment("REQ-02", level=RubricLevel.EXCEEDS, cv_citation=None, cv_location=None)
        gap = make_rubric_assessment("REQ-03", level=RubricLevel.GAP, cv_citation=None, cv_location=None)
        corrected, warnings = enforce_citations([good, bad, gap])
        assert corrected[0].rubric_level == RubricLevel.MEETS
        assert corrected[1].rubric_level == RubricLevel.GAP
        assert corrected[2].rubric_level == RubricLevel.GAP
        assert len(warnings) == 1  # only bad was downgraded


# ---------------------------------------------------------------------------
# assess_candidate tests
# ---------------------------------------------------------------------------


class TestAssessCandidate:
    """Tests for assess_candidate (single candidate, single LLM call)."""

    def _make_valid_response(
        self,
        requirement_ids: list[str],
        candidate_name: str = "Alice",
    ) -> str:
        """Build a valid JSON response for a given set of requirement IDs."""
        data = [
            make_assessment_dict(
                rid,
                candidate_name,
                "meets",
                "high",
                f"Evidence for {rid}",
                "CTO role",
            )
            for rid in requirement_ids
        ]
        return json.dumps(data)

    @pytest.mark.asyncio
    async def test_valid_response_returns_correct_assessments(self) -> None:
        """Mock LLM returns valid JSON → correct RubricAssessment list."""
        reqs = [make_requirement(f"REQ-0{i}", f"Requirement {i}") for i in range(1, 4)]
        req_ids = [r.requirement_id for r in reqs]
        priority_order = [(r, Priority.HIGH) for r in reqs]

        client = MockLLMClient([self._make_valid_response(req_ids)])
        result = await assess_candidate(
            candidate_name="Alice",
            cv_text="Strong CV text",
            requirements=reqs,
            priority_order=priority_order,
            llm_client=client,
        )
        assert len(result) == 3
        assert client.call_count == 1
        for a in result:
            assert a.candidate_name == "Alice"

    @pytest.mark.asyncio
    async def test_drop_detection_fires_follow_up(self) -> None:
        """When LLM drops a requirement, a follow-up call fires automatically."""
        reqs = [
            make_requirement("REQ-01", "Req one"),
            make_requirement("REQ-02", "Req two"),
            make_requirement("REQ-03", "Req three"),
        ]
        priority_order = [(r, Priority.HIGH) for r in reqs]

        # Primary response covers only REQ-01 and REQ-02 (REQ-03 dropped)
        primary = json.dumps(
            [
                make_assessment_dict("REQ-01", "Alice", "meets", "high", "Evidence 1", "CTO role"),
                make_assessment_dict("REQ-02", "Alice", "gap", "high", None, None, None, "Why gap?"),
            ]
        )
        # Follow-up covers REQ-03
        follow_up = json.dumps(
            [
                make_assessment_dict("REQ-03", "Alice", "partial", "medium", "Some evidence", "VP role"),
            ]
        )
        client = MockLLMClient([primary, follow_up])

        result = await assess_candidate(
            candidate_name="Alice",
            cv_text="CV text",
            requirements=reqs,
            priority_order=priority_order,
            llm_client=client,
        )
        assert client.call_count == 2  # primary + follow-up
        assert len(result) == 3
        result_ids = {a.requirement_id for a in result}
        assert result_ids == {"REQ-01", "REQ-02", "REQ-03"}

    @pytest.mark.asyncio
    async def test_citation_enforcement_applied(self) -> None:
        """MEETS without citation → downgraded to GAP."""
        reqs = [make_requirement("REQ-01")]
        priority_order = [(reqs[0], Priority.HIGH)]

        data = [make_assessment_dict("REQ-01", "Alice", "meets", "high", None, None)]
        client = MockLLMClient([json.dumps(data)])

        result = await assess_candidate(
            candidate_name="Alice",
            cv_text="CV text",
            requirements=reqs,
            priority_order=priority_order,
            llm_client=client,
        )
        assert result[0].rubric_level == RubricLevel.GAP

    @pytest.mark.asyncio
    async def test_extra_requirement_ids_filtered(self) -> None:
        """LLM returns assessments for IDs not in input → filtered out."""
        reqs = [make_requirement("REQ-01", "Req one")]
        priority_order = [(reqs[0], Priority.HIGH)]

        data = [
            make_assessment_dict("REQ-01", "Alice", "meets", "high", "Evidence", "Role"),
            make_assessment_dict("REQ-99", "Alice", "exceeds", "high", "Hallucinated", "Role"),
        ]
        client = MockLLMClient([json.dumps(data)])

        result = await assess_candidate(
            candidate_name="Alice",
            cv_text="CV text",
            requirements=reqs,
            priority_order=priority_order,
            llm_client=client,
        )
        assert len(result) == 1
        assert result[0].requirement_id == "REQ-01"


# ---------------------------------------------------------------------------
# assess_all_candidates tests
# ---------------------------------------------------------------------------


class TestAssessAllCandidates:
    """Tests for assess_all_candidates (parallel multi-candidate)."""

    def _make_candidate_response(self, candidate_name: str, req_ids: list[str]) -> str:
        """Build a valid response JSON for a candidate."""
        data = [
            make_assessment_dict(
                rid,
                candidate_name,
                "meets",
                "high",
                f"Evidence for {rid}",
                "CTO role",
            )
            for rid in req_ids
        ]
        return json.dumps(data)

    @pytest.mark.asyncio
    async def test_three_candidates_three_parallel_calls(self) -> None:
        """3 candidates → 3 LLM calls (one per candidate)."""
        reqs = [make_requirement(f"REQ-0{i}", f"Req {i}") for i in range(1, 4)]
        scenario = make_scenario()
        candidates = [
            make_candidate("Alice"),
            make_candidate("Bob"),
            make_candidate("Carol"),
        ]
        req_ids = [r.requirement_id for r in reqs]
        responses = [
            self._make_candidate_response("Alice", req_ids),
            self._make_candidate_response("Bob", req_ids),
            self._make_candidate_response("Carol", req_ids),
        ]
        client = MockLLMClient(responses)

        result = await assess_all_candidates(
            candidates=candidates,
            requirements=reqs,
            scenario=scenario,
            llm_client=client,
        )
        assert client.call_count == 3
        # 3 candidates x 3 requirements = 9 assessments
        assert len(result) == 9

    @pytest.mark.asyncio
    async def test_behavioral_requirements_filtered_out(self) -> None:
        """Behavioral requirements (assessable_from_cv=False) are not sent to LLM."""
        cv_req = make_requirement("REQ-01", "P&L responsibility", assessable=True)
        behavioral_req = make_requirement(
            "REQ-02",
            "Ability to navigate stakeholder environments",
            assessable=False,
        )
        scenario = make_scenario()
        candidate = make_candidate("Alice")

        # Response only covers REQ-01
        response = json.dumps(
            [
                make_assessment_dict("REQ-01", "Alice", "meets", "high", "USD 620M P&L", "CTO role"),
            ]
        )
        client = MockLLMClient([response])

        result = await assess_all_candidates(
            candidates=[candidate],
            requirements=[cv_req, behavioral_req],
            scenario=scenario,
            llm_client=client,
        )
        # Only 1 assessment for the cv_assessable requirement
        assert len(result) == 1
        assert result[0].requirement_id == "REQ-01"

    @pytest.mark.asyncio
    async def test_requirements_ordered_high_first_in_prompt(self) -> None:
        """High-priority requirements appear before low-priority ones in the prompt."""
        # HIGH under digital_transformation = high, LOW = low
        high_req = make_requirement(
            "REQ-01",
            "High-priority req",
            scenario_priority=make_scenario_priority(dt="high"),
        )
        low_req = make_requirement(
            "REQ-02",
            "Low-priority req",
            scenario_priority=make_scenario_priority(dt="low"),
        )
        scenario = make_scenario(ScenarioName.DIGITAL_TRANSFORMATION)
        candidate = make_candidate("Alice")

        response = json.dumps(
            [
                make_assessment_dict("REQ-01", "Alice", "meets", "high", "Evidence", "Role"),
                make_assessment_dict("REQ-02", "Alice", "gap", "high", None, None, None, "Q?"),
            ]
        )
        client = MockLLMClient([response])

        await assess_all_candidates(
            candidates=[candidate],
            requirements=[low_req, high_req],  # deliberately reversed
            scenario=scenario,
            llm_client=client,
        )
        # Inspect the user prompt from the captured call
        assert client.call_count == 1
        _, user_prompt = client.calls[0]
        pos_high = user_prompt.index("REQ-01")
        pos_low = user_prompt.index("REQ-02")
        assert pos_high < pos_low, "HIGH requirement must appear before LOW in prompt"

    @pytest.mark.asyncio
    async def test_no_cv_assessable_requirements_returns_empty(self) -> None:
        """All behavioral requirements → empty assessment list, no LLM calls."""
        behavioral = make_requirement("REQ-01", "Stakeholder management", assessable=False)
        scenario = make_scenario()
        candidate = make_candidate("Alice")
        client = MockLLMClient([])

        result = await assess_all_candidates(
            candidates=[candidate],
            requirements=[behavioral],
            scenario=scenario,
            llm_client=client,
        )
        assert result == []
        assert client.call_count == 0

    @pytest.mark.asyncio
    async def test_flat_list_returned(self) -> None:
        """Result is a flat list, not nested per candidate."""
        reqs = [make_requirement("REQ-01", "Req one")]
        scenario = make_scenario()
        candidates = [make_candidate("Alice"), make_candidate("Bob")]

        client = MockLLMClient(
            [
                json.dumps([make_assessment_dict("REQ-01", "Alice", "meets", "high", "Ev A", "Role")]),
                json.dumps([make_assessment_dict("REQ-01", "Bob", "gap", "high", None, None, None, "Q?")]),
            ]
        )
        result = await assess_all_candidates(
            candidates=candidates,
            requirements=reqs,
            scenario=scenario,
            llm_client=client,
        )
        assert isinstance(result, list)
        assert all(isinstance(a, RubricAssessment) for a in result)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# _build_priority_order tests
# ---------------------------------------------------------------------------


class TestBuildPriorityOrder:
    """Tests for _build_priority_order helper."""

    def test_sorts_high_before_medium_before_low(self) -> None:
        """Requirements come out high → medium → low."""
        req_low = make_requirement("REQ-01", "Low req", scenario_priority=make_scenario_priority(dt="low"))
        req_high = make_requirement("REQ-02", "High req", scenario_priority=make_scenario_priority(dt="high"))
        req_med = make_requirement("REQ-03", "Medium req", scenario_priority=make_scenario_priority(dt="medium"))

        scenario = make_scenario(ScenarioName.DIGITAL_TRANSFORMATION)
        result = _build_priority_order([req_low, req_high, req_med], scenario)

        levels = [p for _, p in result]
        assert levels == [Priority.HIGH, Priority.MEDIUM, Priority.LOW]

    def test_correct_scenario_priority_resolved(self) -> None:
        """Priority is resolved from the active scenario, not a different one."""
        # High under digital_transformation but low under turnaround
        req = make_requirement(
            "REQ-01",
            "Mixed req",
            scenario_priority=make_scenario_priority(dt="high", ta="low"),
        )
        dt_scenario = make_scenario(ScenarioName.DIGITAL_TRANSFORMATION)
        ta_scenario = make_scenario(ScenarioName.TURNAROUND)

        result_dt = _build_priority_order([req], dt_scenario)
        result_ta = _build_priority_order([req], ta_scenario)

        assert result_dt[0][1] == Priority.HIGH
        assert result_ta[0][1] == Priority.LOW


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------


class TestProperties:
    """Hypothesis-based property tests for C3."""

    @given(
        n_cv_assessable=st.integers(min_value=1, max_value=10),
        n_behavioral=st.integers(min_value=0, max_value=5),
    )
    @settings(max_examples=30)
    def test_one_assessment_per_cv_assessable_requirement(
        self,
        n_cv_assessable: int,
        n_behavioral: int,
    ) -> None:
        """Output has exactly one assessment per CV-assessable requirement per candidate."""
        import asyncio

        cv_reqs = [
            make_requirement(f"REQ-{i:02d}", f"CV req {i}", assessable=True) for i in range(1, n_cv_assessable + 1)
        ]
        beh_reqs = [
            make_requirement(
                f"REQ-{n_cv_assessable + j:02d}",
                f"Behavioral req {j}",
                assessable=False,
            )
            for j in range(1, n_behavioral + 1)
        ]
        all_reqs = cv_reqs + beh_reqs
        req_ids = [r.requirement_id for r in cv_reqs]

        candidate = make_candidate("TestCand")
        scenario = make_scenario()

        # Build a valid response for all cv_assessable requirements
        response_data = [make_assessment_dict(rid, "TestCand", "meets", "high", f"Ev {rid}", "Role") for rid in req_ids]
        client = MockLLMClient([json.dumps(response_data)])

        result = asyncio.run(
            assess_all_candidates(
                candidates=[candidate],
                requirements=all_reqs,
                scenario=scenario,
                llm_client=client,
            )
        )

        # Exactly one assessment per cv-assessable requirement
        result_ids = [a.requirement_id for a in result]
        assert sorted(result_ids) == sorted(req_ids)
        # No duplicates
        assert len(result_ids) == len(set(result_ids))
