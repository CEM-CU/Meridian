"""Tests for C3 drop detection: detect_and_fill_drops.

Covers the targeted follow-up LLM call fired when requirements are absent
from the primary batch response.
"""

from __future__ import annotations

import json

import pytest
from _helpers import (
    MockLLMClient,
    make_assessment_dict,
    make_requirement,
)

from meridian.extraction.cv_assessment import detect_and_fill_drops
from meridian.models import (
    Confidence,
    Priority,
    RubricAssessment,
    RubricLevel,
)

# ---------------------------------------------------------------------------
# Drop detection tests
# ---------------------------------------------------------------------------


class TestDetectAndFillDrops:
    """Tests for detect_and_fill_drops."""

    @pytest.mark.asyncio
    async def test_no_missing_ids_returns_original(self) -> None:
        """When no IDs are missing, returns the input list unchanged."""
        assessment = RubricAssessment(
            requirement_id="REQ-01",
            candidate_name="Alice",
            rubric_level=RubricLevel.MEETS,
            confidence=Confidence.HIGH,
            cv_citation="Some evidence",
            cv_location="CTO role",
        )
        req = make_requirement("REQ-01")
        client = MockLLMClient([])
        result = await detect_and_fill_drops(
            assessments=[assessment],
            candidate_name="Alice",
            cv_text="CV text",
            missing_requirement_ids=[],
            requirements=[req],
            priority_order=[(req, Priority.HIGH)],
            llm_client=client,
        )
        assert result == [assessment]
        assert client.call_count == 0

    @pytest.mark.asyncio
    async def test_missing_ids_trigger_follow_up_call(self) -> None:
        """When 2 requirements are missing, one follow-up LLM call fires."""
        existing = RubricAssessment(
            requirement_id="REQ-01",
            candidate_name="Alice",
            rubric_level=RubricLevel.MEETS,
            confidence=Confidence.HIGH,
            cv_citation="Evidence",
            cv_location="Role",
        )
        # Follow-up response covers the 2 missing requirements
        follow_up_data = [
            make_assessment_dict("REQ-02", "Alice", "gap", "high", None, None, None, "Why no EV?"),
            make_assessment_dict("REQ-03", "Alice", "partial", "medium", "Some partial evidence", "VP role"),
        ]
        client = MockLLMClient([json.dumps(follow_up_data)])

        req1 = make_requirement("REQ-01")
        req2 = make_requirement("REQ-02", "EV platform experience")
        req3 = make_requirement("REQ-03", "P&L responsibility")

        result = await detect_and_fill_drops(
            assessments=[existing],
            candidate_name="Alice",
            cv_text="CV text",
            missing_requirement_ids=["REQ-02", "REQ-03"],
            requirements=[req1, req2, req3],
            priority_order=[
                (req1, Priority.HIGH),
                (req2, Priority.HIGH),
                (req3, Priority.MEDIUM),
            ],
            llm_client=client,
        )
        assert client.call_count == 1
        assert len(result) == 3
        result_ids = {a.requirement_id for a in result}
        assert result_ids == {"REQ-01", "REQ-02", "REQ-03"}

    @pytest.mark.asyncio
    async def test_follow_up_citation_enforcement_applied(self) -> None:
        """Citation enforcement is applied to follow-up call results."""
        existing = RubricAssessment(
            requirement_id="REQ-01",
            candidate_name="Alice",
            rubric_level=RubricLevel.MEETS,
            confidence=Confidence.HIGH,
            cv_citation="Evidence",
            cv_location="Role",
        )
        # Follow-up returns MEETS without citation — should be downgraded
        follow_up_data = [
            make_assessment_dict("REQ-02", "Alice", "meets", "high", None, None),
        ]
        client = MockLLMClient([json.dumps(follow_up_data)])

        req1 = make_requirement("REQ-01")
        req2 = make_requirement("REQ-02", "EV experience")

        result = await detect_and_fill_drops(
            assessments=[existing],
            candidate_name="Alice",
            cv_text="CV text",
            missing_requirement_ids=["REQ-02"],
            requirements=[req1, req2],
            priority_order=[(req1, Priority.HIGH), (req2, Priority.MEDIUM)],
            llm_client=client,
        )
        req02_assessment = next(a for a in result if a.requirement_id == "REQ-02")
        assert req02_assessment.rubric_level == RubricLevel.GAP  # downgraded
