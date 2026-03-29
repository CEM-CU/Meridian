"""Tests for C1: JD requirement extraction.

Covers prompt building, LLM response parsing, all 4 validation checks,
count warnings, and the full async orchestrator with a mocked LLM client.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from shared.models import Priority, Requirement, ScenarioPriority
from stage_c.jd_extraction import (
    _keyword_overlap,
    count_warnings,
    extract_requirements,
    parse_llm_response,
    validate_extracted_requirements,
)
from stage_c.prompts.jd_extraction import (
    REQUIREMENT_JSON_SCHEMA,
    build_jd_extraction_prompt,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_scenario_priority(
    dt: str = "high",
    pa: str = "medium",
    ta: str = "low",
    st: str = "medium",
    gr: str = "high",
) -> ScenarioPriority:
    """Create a ScenarioPriority with convenient defaults."""
    return ScenarioPriority(
        digital_transformation=Priority(dt),
        post_acquisition=Priority(pa),
        turnaround=Priority(ta),
        stabilization=Priority(st),
        growth=Priority(gr),
    )


def _make_requirement(
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
        scenario_priority=scenario_priority or _make_scenario_priority(),
    )


def _make_valid_requirement_dicts(count: int = 3) -> list[dict[str, Any]]:
    """Create a list of valid requirement dicts for JSON serialization."""
    reqs: list[dict[str, Any]] = []
    texts = [
        "10+ years technology leadership experience",
        "P&L responsibility exceeding $100M",
        "Experience with cloud migration at enterprise scale",
        "Board-level presentation skills",
        "Track record of building high-performing engineering teams",
    ]
    for i in range(count):
        reqs.append(
            {
                "requirement_id": f"REQ-{i + 1:02d}",
                "text": texts[i % len(texts)],
                "source_quote": f"Source quote for requirement {i + 1}",
                "assessable_from_cv": i != 3,  # REQ-04 is behavioral
                "scenario_priority": {
                    "digital_transformation": "high",
                    "post_acquisition": "medium",
                    "turnaround": "low",
                    "stabilization": "medium",
                    "growth": "high",
                },
            }
        )
    return reqs


# ---------------------------------------------------------------------------
# Prompt builder tests
# ---------------------------------------------------------------------------


class TestBuildJdExtractionPrompt:
    """Tests for the prompt builder function."""

    def test_returns_two_strings(self) -> None:
        """Prompt builder returns a (system, user) tuple."""
        system, user = build_jd_extraction_prompt("Some JD text")
        assert isinstance(system, str)
        assert isinstance(user, str)

    def test_system_prompt_contains_key_instructions(self) -> None:
        """System prompt includes extraction guidance."""
        system, _ = build_jd_extraction_prompt("JD")
        assert "compound" in system.lower()
        assert "implicit" in system.lower()
        assert "boilerplate" in system.lower()
        assert "assessable_from_cv" in system
        assert "scenario_priority" in system
        assert "sequential" in system.lower() or "REQ-01" in system

    def test_system_prompt_contains_all_scenarios(self) -> None:
        """System prompt describes all 5 scenarios."""
        system, _ = build_jd_extraction_prompt("JD")
        assert "digital_transformation" in system
        assert "post_acquisition" in system
        assert "turnaround" in system
        assert "stabilization" in system
        assert "growth" in system

    def test_system_prompt_contains_json_schema(self) -> None:
        """System prompt includes the expected JSON schema."""
        system, _ = build_jd_extraction_prompt("JD")
        assert "requirement_id" in system
        assert "source_quote" in system

    def test_user_prompt_contains_jd_text(self) -> None:
        """User prompt includes the provided JD text."""
        jd = "Chief Technology Officer at Acme Corp"
        _, user = build_jd_extraction_prompt(jd)
        assert jd in user

    def test_schema_constant_is_valid_json_structure(self) -> None:
        """The schema constant parses as JSON."""
        parsed = json.loads(REQUIREMENT_JSON_SCHEMA)
        assert isinstance(parsed, list)
        assert "requirement_id" in parsed[0]


# ---------------------------------------------------------------------------
# parse_llm_response tests
# ---------------------------------------------------------------------------


class TestParseLlmResponse:
    """Tests for LLM response parsing."""

    def test_valid_json_produces_requirements(self) -> None:
        """Valid JSON array produces correct Requirement list."""
        dicts = _make_valid_requirement_dicts(3)
        raw = json.dumps(dicts)
        result = parse_llm_response(raw)
        assert len(result) == 3
        assert all(isinstance(r, Requirement) for r in result)
        assert result[0].requirement_id == "REQ-01"
        assert result[1].requirement_id == "REQ-02"

    def test_valid_json_with_markdown_fences(self) -> None:
        """JSON wrapped in markdown code fences is parsed correctly."""
        dicts = _make_valid_requirement_dicts(2)
        raw = f"```json\n{json.dumps(dicts)}\n```"
        result = parse_llm_response(raw)
        assert len(result) == 2

    def test_markdown_fence_without_newline(self) -> None:
        """Malformed markdown fence without newline is handled gracefully."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_llm_response("```json")

    def test_markdown_fence_bare_backticks(self) -> None:
        """Bare triple backticks with no content are handled gracefully."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_llm_response("```")

    def test_invalid_json_raises_value_error(self) -> None:
        """Malformed JSON raises ValueError."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_llm_response("{not valid json]")

    def test_non_array_raises_value_error(self) -> None:
        """JSON object (not array) raises ValueError."""
        with pytest.raises(ValueError, match="Expected JSON array"):
            parse_llm_response('{"key": "value"}')

    def test_invalid_requirement_schema_raises_value_error(self) -> None:
        """Requirement with missing fields raises ValueError."""
        raw = json.dumps([{"requirement_id": "REQ-01"}])
        with pytest.raises(ValueError, match="failed validation"):
            parse_llm_response(raw)

    def test_all_fields_populated(self) -> None:
        """Parsed requirements have all expected fields."""
        dicts = _make_valid_requirement_dicts(1)
        result = parse_llm_response(json.dumps(dicts))
        req = result[0]
        assert req.text
        assert req.source_quote
        assert isinstance(req.assessable_from_cv, bool)
        assert req.scenario_priority.digital_transformation == Priority.HIGH


# ---------------------------------------------------------------------------
# Validation check 1: Sequential IDs
# ---------------------------------------------------------------------------


class TestCheckSequentialIds:
    """Tests for sequential ID validation."""

    def test_sequential_ids_no_warning(self) -> None:
        """Sequential IDs produce no warnings."""
        reqs = [_make_requirement(req_id=f"REQ-{i + 1:02d}") for i in range(3)]
        _, warnings = validate_extracted_requirements(reqs)
        id_warnings = [w for w in warnings if "sequential" in w.lower() or "ID" in w]
        assert not id_warnings

    def test_non_sequential_ids_produce_warning(self) -> None:
        """Non-sequential IDs (REQ-01, REQ-03) produce a warning."""
        reqs = [
            _make_requirement(req_id="REQ-01"),
            _make_requirement(req_id="REQ-03", text="Different requirement text"),
        ]
        _, warnings = validate_extracted_requirements(reqs)
        assert any("REQ-03" in w for w in warnings)

    def test_invalid_id_format_produces_warning(self) -> None:
        """IDs not matching REQ-NN format produce a warning."""
        reqs = [_make_requirement(req_id="R01")]
        _, warnings = validate_extracted_requirements(reqs)
        assert any("R01" in w for w in warnings)


# ---------------------------------------------------------------------------
# Validation check 2: Duplicate detection
# ---------------------------------------------------------------------------


class TestCheckDuplicates:
    """Tests for duplicate requirement detection."""

    def test_high_overlap_produces_warning(self) -> None:
        """Two requirements with >60% keyword overlap trigger a warning."""
        reqs = [
            _make_requirement(
                req_id="REQ-01",
                text="Experience leading digital transformation initiatives",
            ),
            _make_requirement(
                req_id="REQ-02",
                text="Experience leading digital transformation programs",
            ),
        ]
        _, warnings = validate_extracted_requirements(reqs)
        assert any("duplicate" in w.lower() for w in warnings)

    def test_low_overlap_no_warning(self) -> None:
        """Two distinct requirements do not trigger duplicate warning."""
        reqs = [
            _make_requirement(req_id="REQ-01", text="P&L responsibility exceeding $500M"),
            _make_requirement(req_id="REQ-02", text="Cloud architecture migration experience"),
        ]
        _, warnings = validate_extracted_requirements(reqs)
        assert not any("duplicate" in w.lower() for w in warnings)


# ---------------------------------------------------------------------------
# Validation check 3: Routing consistency
# ---------------------------------------------------------------------------


class TestCheckRoutingConsistency:
    """Tests for behavioral routing auto-correction."""

    def test_behavioral_marked_assessable_is_corrected(self) -> None:
        """Behavioral requirement with assessable_from_cv=True is auto-corrected to False."""
        reqs = [
            _make_requirement(
                req_id="REQ-01",
                text="Strong interpersonal communication and leadership style",
                assessable=True,
            ),
        ]
        corrected, warnings = validate_extracted_requirements(reqs)
        assert corrected[0].assessable_from_cv is False
        assert any("auto-corrected" in w for w in warnings)

    def test_non_behavioral_assessable_unchanged(self) -> None:
        """Non-behavioral requirement with assessable_from_cv=True is not changed."""
        reqs = [
            _make_requirement(
                req_id="REQ-01",
                text="10+ years P&L responsibility exceeding $500M",
                assessable=True,
            ),
        ]
        corrected, warnings = validate_extracted_requirements(reqs)
        assert corrected[0].assessable_from_cv is True
        assert not any("auto-corrected" in w for w in warnings)

    def test_original_not_mutated(self) -> None:
        """Validation does not mutate the original requirement list."""
        original = _make_requirement(
            req_id="REQ-01",
            text="Strong interpersonal communication and leadership style",
            assessable=True,
        )
        reqs = [original]
        corrected, _ = validate_extracted_requirements(reqs)
        # Original is still True
        assert original.assessable_from_cv is True
        # Corrected is False
        assert corrected[0].assessable_from_cv is False


# ---------------------------------------------------------------------------
# Validation check 4: Priority validation
# ---------------------------------------------------------------------------


class TestCheckPriorityValues:
    """Tests for scenario priority value validation."""

    def test_valid_priorities_no_warning(self) -> None:
        """All valid Priority enum values produce no warnings."""
        reqs = [_make_requirement()]
        _, warnings = validate_extracted_requirements(reqs)
        priority_warnings = [w for w in warnings if "invalid priority" in w.lower()]
        assert not priority_warnings

    def test_all_scenarios_present(self) -> None:
        """Requirements with all 5 scenario priorities pass validation."""
        reqs = [_make_requirement()]
        _, warnings = validate_extracted_requirements(reqs)
        scenario_warnings = [w for w in warnings if "missing scenario" in w.lower()]
        assert not scenario_warnings


# ---------------------------------------------------------------------------
# count_warnings tests
# ---------------------------------------------------------------------------


class TestCountWarnings:
    """Tests for requirement count warnings."""

    def test_too_few_requirements_warns(self) -> None:
        """5 requirements triggers 'too vague' warning."""
        reqs = [_make_requirement(req_id=f"REQ-{i + 1:02d}") for i in range(5)]
        warnings = count_warnings(reqs)
        assert len(warnings) == 1
        assert "vague" in warnings[0].lower()

    def test_too_many_requirements_warns(self) -> None:
        """20 requirements triggers 'consolidation' warning."""
        reqs = [_make_requirement(req_id=f"REQ-{i + 1:02d}") for i in range(20)]
        warnings = count_warnings(reqs)
        assert len(warnings) == 1
        assert "consolidat" in warnings[0].lower()

    def test_normal_count_no_warning(self) -> None:
        """12 requirements triggers no warning."""
        reqs = [_make_requirement(req_id=f"REQ-{i + 1:02d}") for i in range(12)]
        warnings = count_warnings(reqs)
        assert not warnings

    def test_boundary_six_no_warning(self) -> None:
        """6 requirements (boundary) triggers no warning."""
        reqs = [_make_requirement(req_id=f"REQ-{i + 1:02d}") for i in range(6)]
        warnings = count_warnings(reqs)
        assert not warnings

    def test_boundary_eighteen_no_warning(self) -> None:
        """18 requirements (boundary) triggers no warning."""
        reqs = [_make_requirement(req_id=f"REQ-{i + 1:02d}") for i in range(18)]
        warnings = count_warnings(reqs)
        assert not warnings


# ---------------------------------------------------------------------------
# Keyword overlap helper tests
# ---------------------------------------------------------------------------


class TestKeywordOverlap:
    """Tests for the keyword overlap helper."""

    def test_identical_texts_full_overlap(self) -> None:
        """Identical texts produce 1.0 overlap."""
        assert _keyword_overlap("digital transformation", "digital transformation") == 1.0

    def test_disjoint_texts_zero_overlap(self) -> None:
        """Completely different texts produce 0.0 overlap."""
        assert _keyword_overlap("cloud architecture", "financial reporting") == 0.0

    def test_empty_texts_zero_overlap(self) -> None:
        """Empty texts produce 0.0 overlap."""
        assert _keyword_overlap("", "") == 0.0

    def test_stopwords_filtered(self) -> None:
        """Stopwords are excluded from overlap computation."""
        # "the" and "and" are stopwords, so only content words matter
        overlap = _keyword_overlap("the big dog and cat", "the small dog and bird")
        # keywords: {big, dog, cat} vs {small, dog, bird} → 1/5 = 0.2
        assert 0.1 < overlap < 0.3

    def test_partial_overlap(self) -> None:
        """Partial overlap returns expected ratio."""
        overlap = _keyword_overlap(
            "experience leading digital transformation",
            "experience leading digital programs",
        )
        # keywords: {experience, leading, digital, transformation} vs {experience, leading, digital, programs}
        # intersection: 3, union: 5 → 0.6
        assert 0.5 < overlap < 0.7


# ---------------------------------------------------------------------------
# Full orchestrator test
# ---------------------------------------------------------------------------


class TestExtractRequirements:
    """Tests for the full C1 orchestrator with mocked LLM client."""

    @pytest.fixture()
    def mock_llm_response(self) -> str:
        """Valid LLM response JSON for 3 requirements."""
        return json.dumps(_make_valid_requirement_dicts(3))

    @pytest.fixture()
    def mock_llm_client(self, mock_llm_response: str) -> Any:
        """Mock LLM client that returns a fixed response."""

        class MockClient:
            async def complete(self, system: str, user: str) -> str:
                return mock_llm_response

        return MockClient()

    async def test_orchestrator_returns_requirements_and_warnings(self, mock_llm_client: Any) -> None:
        """Full pipeline returns validated requirements and warnings list."""
        reqs, warnings = await extract_requirements(
            jd_text="CTO position at Acme Corp requiring 10 years experience",
            llm_client=mock_llm_client,
        )
        assert len(reqs) == 3
        assert all(isinstance(r, Requirement) for r in reqs)
        assert isinstance(warnings, list)

    async def test_orchestrator_requirements_have_valid_ids(self, mock_llm_client: Any) -> None:
        """Orchestrator output has sequential requirement IDs."""
        reqs, _ = await extract_requirements(
            jd_text="JD text",
            llm_client=mock_llm_client,
        )
        ids = [r.requirement_id for r in reqs]
        assert ids == ["REQ-01", "REQ-02", "REQ-03"]

    async def test_orchestrator_requirements_have_scenario_priorities(self, mock_llm_client: Any) -> None:
        """All requirements have valid scenario_priority with all 5 scenarios."""
        reqs, _ = await extract_requirements(
            jd_text="JD text",
            llm_client=mock_llm_client,
        )
        for req in reqs:
            sp = req.scenario_priority
            assert sp.digital_transformation in Priority
            assert sp.post_acquisition in Priority
            assert sp.turnaround in Priority
            assert sp.stabilization in Priority
            assert sp.growth in Priority

    async def test_orchestrator_count_warning_for_few_requirements(self) -> None:
        """Orchestrator includes count warning when too few requirements extracted."""
        few_reqs = _make_valid_requirement_dicts(4)

        class FewClient:
            async def complete(self, system: str, user: str) -> str:
                return json.dumps(few_reqs)

        reqs, warnings = await extract_requirements(jd_text="Brief JD", llm_client=FewClient())
        assert len(reqs) == 4
        assert any("vague" in w.lower() for w in warnings)

    async def test_orchestrator_invalid_llm_response_raises(self) -> None:
        """Orchestrator raises ValueError on invalid LLM response."""

        class BadClient:
            async def complete(self, system: str, user: str) -> str:
                return "not json at all"

        with pytest.raises(ValueError, match="Invalid JSON"):
            await extract_requirements(jd_text="JD", llm_client=BadClient())
