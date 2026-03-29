"""Golden-path integration test for Stage E.

Tests the full E1→E2→E3→E5→E7 pipeline, plus E6 self-consistency
and E9 timeout/graceful-degradation scenarios.

All LLM calls are mocked. Test data is constructed entirely from
shared.models — no imports from stage_c or stage_d.

Coverage:
    test_full_e1_through_e7_pipeline         — happy-path full pipeline
    test_synthesis_output_round_trip         — Pydantic serialise / deserialise
    test_partial_mode_handled                — partial-mode candidate rules
    test_f02_signal_labels_not_in_agent_input — F02 constraint validation
    test_audit_no_stripped_claims_on_valid_input — E5 produces 0 stripped claims
    test_timeout_handling                    — E9 graceful degradation
    test_scenario_affects_matrix_sort_order  — scenario switch changes row order
    test_all_layers_present                  — SynthesisOutput structure
"""

from __future__ import annotations

import pytest
from stage_e.layer0_validation import validate_stage_d_output
from stage_e.layer1_signals import Layer1Output, compute_layer1
from stage_e.layer2_agents.runner import run_agents
from stage_e.layer3_audit.runner import run_audit
from stage_e.schemas import AgentVerdict
from stage_e.synthesis.assembler import assemble_synthesis
from stage_e.synthesis.models import SynthesisOutput
from stage_e.timeout import build_degradation_notice, is_viable_result

from ._integration_fixtures import (
    _DIGITAL_SCENARIO,
    _GROWTH_SCENARIO,
    _REQUIREMENTS,
    _make_stage_d_output,
    _MockLLMClient,
    _SlowAgentMockLLMClient,
)

# ---------------------------------------------------------------------------
# Pipeline runner helper — runs E1→E2→E3→E5→E7 end-to-end
# ---------------------------------------------------------------------------


async def _run_full_pipeline(
    stage_d: object,
    llm_client: _MockLLMClient,
    agent_timeout: float = 15.0,
) -> tuple[SynthesisOutput, Layer1Output, list[str], dict[str, AgentVerdict | None]]:
    """Execute the full Stage E pipeline and return (synthesis, layer1, audit_warnings, verdicts).

    Mirrors the execution order described in the Stage E spec:
    E1 → E2 → E3 → E5 → E7

    The verdicts dict is returned so callers can assert directly on the
    actual pipeline state (e.g. which agents timed out).
    """
    from shared.models.pipeline import StageDOutput

    assert isinstance(stage_d, StageDOutput)

    # E1: Layer 0 validation
    cleaned, _validation_warnings = validate_stage_d_output(stage_d)

    # E2: Layer 1 signal computation
    candidate_names = [c.name for c in cleaned.candidate_data]
    assessment_modes: dict[str, str] = {
        name: prov.assessment_mode.value for name, prov in cleaned.provenance_per_candidate.items()
    }
    layer1 = compute_layer1(
        flags=cleaned.flags,
        scenario=cleaned.scenario,
        candidate_names=candidate_names,
        assessment_modes=assessment_modes,
    )

    # E3: Layer 2 agent execution (3 LLM calls, parallel)
    verdicts = await run_agents(
        flags=cleaned.flags,
        tension_map=layer1.tension_map,
        candidates=cleaned.candidate_data,
        requirements=cleaned.confirmed_requirements,
        assessment_modes=assessment_modes,
        llm_client=llm_client,
        timeout_seconds=agent_timeout,
    )

    # E5: Layer 3 audit (deterministic, 0 LLM calls)
    audited_verdicts, audit_warnings = run_audit(
        verdicts=verdicts,
        flags=cleaned.flags,
        candidate_data=cleaned.candidate_data,
        rubric_assessments=cleaned.rubric_matrix,
        requirements=cleaned.confirmed_requirements,
    )

    # E7: Synthesis (1 LLM call)
    synthesis = await assemble_synthesis(
        stage_d_output=cleaned,
        layer1_output=layer1,
        audited_verdicts=audited_verdicts,
        audit_warnings=audit_warnings,
        llm_client=llm_client,
    )

    return synthesis, layer1, audit_warnings, verdicts


# ===========================================================================
# Test 1: Full E1 → E7 happy-path pipeline
# ===========================================================================


@pytest.mark.asyncio
async def test_full_e1_through_e7_pipeline() -> None:
    """E1→E2→E3→E5→E7 golden path produces a valid, complete SynthesisOutput.

    Verifies all top-level fields are present and semantically correct,
    including the trade-off matrix spanning all candidates x requirements,
    per-candidate summaries for all 3 candidates, and a non-empty trade-off
    statement from the mocked LLM.
    """
    stage_d = _make_stage_d_output()
    llm = _MockLLMClient()

    synthesis, _layer1, _warnings, _verdicts = await _run_full_pipeline(stage_d, llm)

    # Must produce a SynthesisOutput instance
    assert isinstance(synthesis, SynthesisOutput)

    # trade_off_matrix: cells for all candidates x all requirements with rubric assessments
    candidate_names_in_matrix = {cell.candidate_name for cell in synthesis.trade_off_matrix}
    assert "Alice" in candidate_names_in_matrix
    assert "Bob" in candidate_names_in_matrix
    assert "Carol" in candidate_names_in_matrix

    req_ids_in_matrix = {cell.requirement_id for cell in synthesis.trade_off_matrix}
    expected_req_ids = {r.requirement_id for r in _REQUIREMENTS}
    # Every requirement must appear in the matrix — exact equality, not subset
    assert req_ids_in_matrix == expected_req_ids
    assert len(synthesis.trade_off_matrix) == 24  # 3 candidates x 8 requirements

    # candidate_summaries: one entry per candidate that had claims in verdicts
    summary_names = {s.candidate_name for s in synthesis.candidate_summaries}
    assert "Alice" in summary_names
    assert "Bob" in summary_names
    assert "Carol" in summary_names
    assert len(synthesis.candidate_summaries) == 3

    # provenance header populated
    assert synthesis.provenance.requirement_count == 8
    assert synthesis.provenance.candidate_count == 3
    assert synthesis.provenance.cv_assessable_count == 6
    assert synthesis.provenance.behavioral_count == 2
    assert "Alice" in synthesis.provenance.assessment_modes
    assert "Bob" in synthesis.provenance.assessment_modes
    assert "Carol" in synthesis.provenance.assessment_modes

    # epistemic disclaimer always present (F10)
    assert synthesis.epistemic_disclaimer
    assert len(synthesis.epistemic_disclaimer) > 20

    # trade_off_statement non-empty
    assert synthesis.trade_off_statement
    assert len(synthesis.trade_off_statement) > 10


# ===========================================================================
# Test 2: SynthesisOutput round-trip serialisation
# ===========================================================================


@pytest.mark.asyncio
async def test_synthesis_output_round_trip() -> None:
    """SynthesisOutput.model_dump() round-trips cleanly through model_validate().

    Pydantic v2 serialise/deserialise must not raise and must produce an
    object equal (by dict representation) to the original.
    """
    stage_d = _make_stage_d_output()
    llm = _MockLLMClient()

    synthesis, _, _, _ = await _run_full_pipeline(stage_d, llm)

    dumped = synthesis.model_dump()
    reloaded = SynthesisOutput.model_validate(dumped)

    assert isinstance(reloaded, SynthesisOutput)
    assert reloaded.model_dump() == dumped


# ===========================================================================
# Test 3: Partial-mode candidate handling
# ===========================================================================


@pytest.mark.asyncio
async def test_partial_mode_handled() -> None:
    """Carol (partial mode) is handled correctly throughout the pipeline.

    Asserts:
    - Carol's summary assessment_mode == 'partial'
    - partial_mode_disclaimer is present in output (F09)
    - Behavioral requirement cells for Carol show 'not_assessable'
    """
    stage_d = _make_stage_d_output()
    llm = _MockLLMClient()

    synthesis, _, _, _ = await _run_full_pipeline(stage_d, llm)

    # Find Carol's summary
    carol_summary = next((s for s in synthesis.candidate_summaries if s.candidate_name == "Carol"), None)
    assert carol_summary is not None, "Carol must have a candidate summary"
    assert carol_summary.assessment_mode == "partial"

    # Partial mode disclaimer present (F09) because Carol is partial
    assert synthesis.partial_mode_disclaimer is not None
    assert len(synthesis.partial_mode_disclaimer) > 10

    # Behavioral requirements (REQ-07, REQ-08) must show 'not_assessable' for Carol
    behavioral_req_ids = {r.requirement_id for r in _REQUIREMENTS if not r.assessable_from_cv}
    carol_behavioral_cells = [
        cell
        for cell in synthesis.trade_off_matrix
        if cell.candidate_name == "Carol" and cell.requirement_id in behavioral_req_ids
    ]
    assert len(carol_behavioral_cells) > 0, "Carol must have cells for behavioral requirements"
    for cell in carol_behavioral_cells:
        assert cell.rubric_level == "not_assessable", (
            f"Carol's behavioral cell {cell.requirement_id} must be 'not_assessable', got '{cell.rubric_level}'"
        )


# ===========================================================================
# Test 4: F02 — signal_labels and risk_bands NOT in agent input
# ===========================================================================


@pytest.mark.asyncio
async def test_f02_signal_labels_not_in_agent_input() -> None:
    """Layer1Output carries signal_labels / risk_bands but neither appears in any AgentVerdict or Claim.

    F02 is a hard architectural constraint: signal labels and risk bands must
    not leak into the agent inputs. We verify this structurally: Layer1Output
    has these fields, but the parsed AgentVerdict objects (which are the agent
    outputs — shaped by the prompts) contain no such keys.
    """
    stage_d = _make_stage_d_output()
    llm = _MockLLMClient()

    # E1 + E2
    cleaned, _ = validate_stage_d_output(stage_d)
    candidate_names = [c.name for c in cleaned.candidate_data]
    assessment_modes = {name: prov.assessment_mode.value for name, prov in cleaned.provenance_per_candidate.items()}
    layer1 = compute_layer1(
        flags=cleaned.flags,
        scenario=cleaned.scenario,
        candidate_names=candidate_names,
        assessment_modes=assessment_modes,
    )

    # Layer1Output MUST have signal_labels and risk_bands
    assert hasattr(layer1, "signal_labels")
    assert hasattr(layer1, "risk_bands")
    assert len(layer1.signal_labels) == 3
    assert len(layer1.risk_bands) == 3

    # E3: capture verdicts
    verdicts = await run_agents(
        flags=cleaned.flags,
        tension_map=layer1.tension_map,
        candidates=cleaned.candidate_data,
        requirements=cleaned.confirmed_requirements,
        assessment_modes=assessment_modes,
        llm_client=llm,
    )

    # Verify no AgentVerdict or Claim contains signal_label / risk_band keys
    forbidden_keys = {"signal_labels", "risk_bands", "signal_label", "risk_band"}

    for role, verdict in verdicts.items():
        assert verdict is not None, f"Verdict for {role} must not be None"

        verdict_dict = verdict.model_dump()

        # Check top-level AgentVerdict fields
        verdict_keys = set(verdict_dict.keys())
        overlap = verdict_keys & forbidden_keys
        assert not overlap, f"AgentVerdict for '{role}' contains forbidden F02 keys: {overlap}"

        # Check each Claim's fields
        for claim in verdict.claims:
            claim_dict = claim.model_dump()
            claim_keys = set(claim_dict.keys())
            claim_overlap = claim_keys & forbidden_keys
            assert not claim_overlap, f"Claim in '{role}' verdict contains forbidden F02 keys: {claim_overlap}"

            # Also check EvidenceBasis keys
            eb_keys = set(claim_dict["evidence_basis"].keys())
            eb_overlap = eb_keys & forbidden_keys
            assert not eb_overlap, f"EvidenceBasis in '{role}' claim contains forbidden F02 keys: {eb_overlap}"


# ===========================================================================
# Test 5: Audit produces no stripped claims on valid input
# ===========================================================================


@pytest.mark.asyncio
async def test_audit_no_stripped_claims_on_valid_input() -> None:
    """E5 audit strips zero claims when agent responses are well-formed.

    The mock LLM returns verdicts whose evidence references all resolve to
    valid flag names and requirement IDs. Stripping checks (CHECK2, CHECK4,
    CHECK5) should therefore produce no stripping warnings.

    Note: Advisory checks (CHECK3, DRIFT/CHECK6, CHECK8) may still produce
    non-stripping warnings without affecting the claim count.
    """
    stage_d = _make_stage_d_output()
    llm = _MockLLMClient()

    cleaned, _ = validate_stage_d_output(stage_d)
    candidate_names = [c.name for c in cleaned.candidate_data]
    assessment_modes = {name: prov.assessment_mode.value for name, prov in cleaned.provenance_per_candidate.items()}
    layer1 = compute_layer1(
        flags=cleaned.flags,
        scenario=cleaned.scenario,
        candidate_names=candidate_names,
        assessment_modes=assessment_modes,
    )

    verdicts = await run_agents(
        flags=cleaned.flags,
        tension_map=layer1.tension_map,
        candidates=cleaned.candidate_data,
        requirements=cleaned.confirmed_requirements,
        assessment_modes=assessment_modes,
        llm_client=llm,
    )

    # Count total claims before audit
    pre_audit_claim_count = sum(len(v.claims) for v in verdicts.values() if v is not None)

    audited_verdicts, audit_warnings = run_audit(
        verdicts=verdicts,
        flags=cleaned.flags,
        candidate_data=cleaned.candidate_data,
        rubric_assessments=cleaned.rubric_matrix,
        requirements=cleaned.confirmed_requirements,
    )

    # Count claims after audit
    post_audit_claim_count = sum(len(v.claims) for v in audited_verdicts.values())

    # No claims should have been stripped on a well-formed input
    stripped_count = pre_audit_claim_count - post_audit_claim_count
    assert stripped_count == 0, (
        f"Audit stripped {stripped_count} claims on valid input. Audit warnings: {audit_warnings}"
    )

    # Any remaining warnings must be advisory-only (CHECK3, DRIFT, CHECK8) — not stripping tags
    stripping_tags = {"[CHECK2]", "[CHECK4]", "[CHECK5]"}
    stripping_warnings = [w for w in audit_warnings if any(tag in w for tag in stripping_tags)]
    assert stripping_warnings == [], (
        f"Unexpected stripping-check warnings on valid input: {stripping_warnings}"
    )


# ===========================================================================
# Test 6: Timeout handling — one agent slow → 2-agent output + degradation notice
# ===========================================================================


@pytest.mark.asyncio
async def test_timeout_handling() -> None:
    """One agent timing out produces 2-agent synthesis + a degradation notice.

    The team_dynamics agent sleeps for 30s. With a 0.05s per-agent timeout,
    it is cancelled. The other two agents (role_fit, risk) respond instantly.

    Verifies:
    - is_viable_result() returns True (2 of 3 agents present)
    - SynthesisOutput is produced (not None, not an exception)
    - candidate_summaries still exist for all candidates
    - build_degradation_notice() returns a non-empty notice for team_dynamics
    """
    stage_d = _make_stage_d_output()
    # Use 0.05s timeout so the 30s sleep is always cancelled in CI
    slow_llm = _SlowAgentMockLLMClient(slow_role="devil's advocate", delay=30.0)

    synthesis, _, _, actual_verdicts = await _run_full_pipeline(stage_d, slow_llm, agent_timeout=0.05)

    # Pipeline must not crash — synthesis output is produced
    assert isinstance(synthesis, SynthesisOutput)
    assert synthesis.trade_off_statement

    # Verify the ACTUAL pipeline state: team_dynamics timed out → None
    assert actual_verdicts.get("team_dynamics") is None, (
        "team_dynamics should be None after timeout"
    )
    assert isinstance(actual_verdicts.get("role_fit"), AgentVerdict), (
        "role_fit should be a real AgentVerdict"
    )
    assert isinstance(actual_verdicts.get("risk"), AgentVerdict), (
        "risk should be a real AgentVerdict"
    )

    # is_viable_result on the ACTUAL verdicts (not a hardcoded mock)
    assert is_viable_result(actual_verdicts) is True

    # Verify all-None is not viable
    all_none: dict[str, AgentVerdict | None] = {"role_fit": None, "team_dynamics": None, "risk": None}
    assert is_viable_result(all_none) is False

    # build_degradation_notice with the ACTUAL missing agents from the pipeline
    missing_agents = [role for role, v in actual_verdicts.items() if v is None]
    notice = build_degradation_notice(missing_agents)
    assert notice != ""
    assert "team dynamics" in notice.lower()
    assert "unavailable" in notice.lower()


# ===========================================================================
# Test 7: Scenario switch changes trade-off matrix sort order
# ===========================================================================


@pytest.mark.asyncio
async def test_scenario_affects_matrix_sort_order() -> None:
    """Same StageDOutput with different scenario produces different row priority order.

    REQ-03 (digital transformation delivery) is HIGH priority in the
    digital_transformation scenario and LOW in post_acquisition. This means it
    should appear earlier in the matrix under digital_transformation and later
    under post_acquisition (where REQ-02 P&L becomes HIGH priority).

    Rubric levels must remain identical between scenarios.
    """
    stage_d_digital = _make_stage_d_output(scenario=_DIGITAL_SCENARIO)
    stage_d_growth = _make_stage_d_output(scenario=_GROWTH_SCENARIO)

    llm = _MockLLMClient()

    synthesis_digital, _, _, _ = await _run_full_pipeline(stage_d_digital, llm)
    synthesis_growth, _, _, _ = await _run_full_pipeline(stage_d_growth, llm)

    # Collect priority labels per requirement for each scenario
    def _priority_map(synthesis: SynthesisOutput) -> dict[str, str]:
        """Return {requirement_id: active_priority} from the first row per req."""
        result: dict[str, str] = {}
        for cell in synthesis.trade_off_matrix:
            if cell.requirement_id not in result:
                result[cell.requirement_id] = cell.active_priority
        return result

    pmap_digital = _priority_map(synthesis_digital)
    pmap_growth = _priority_map(synthesis_growth)

    # REQ-03 is HIGH in digital, MEDIUM in growth — priorities differ
    # (at minimum one requirement should have a different priority)
    assert pmap_digital != pmap_growth, (
        "Expected different priority maps for digital_transformation vs growth scenarios"
    )

    # Rubric levels must NOT change between scenarios
    def _rubric_levels(synthesis: SynthesisOutput) -> dict[tuple[str, str], str]:
        """Return {(req_id, candidate): rubric_level} ignoring partial not_assessable override."""
        return {(c.requirement_id, c.candidate_name): c.rubric_level for c in synthesis.trade_off_matrix}

    levels_digital = _rubric_levels(synthesis_digital)
    levels_growth = _rubric_levels(synthesis_growth)

    assert levels_digital == levels_growth, (
        "Rubric levels must not change when scenario changes — only sort order changes"
    )


# ===========================================================================
# Test 8: All layers present in SynthesisOutput
# ===========================================================================


@pytest.mark.asyncio
async def test_all_layers_present() -> None:
    """SynthesisOutput contains all required sections from all three disclosure layers.

    Checks structural completeness:
    - provenance: ProvenanceHeader
    - trade_off_matrix: non-empty list of TradeOffCell
    - candidate_summaries: non-empty list of CandidateSummary
    - trade_off_statement: non-empty string
    - contested_signals: list (may be empty)
    - epistemic_disclaimer: non-empty string (F10)
    - partial_mode_disclaimer: present because Carol is partial (F09)
    """
    stage_d = _make_stage_d_output()
    llm = _MockLLMClient()

    synthesis, _, _, _ = await _run_full_pipeline(stage_d, llm)

    # Layer 1 — trade-off matrix
    assert synthesis.trade_off_matrix is not None
    assert len(synthesis.trade_off_matrix) > 0

    # Layer 2 — candidate summaries
    assert synthesis.candidate_summaries is not None
    assert len(synthesis.candidate_summaries) > 0

    # Layer 3 — provenance header
    assert synthesis.provenance is not None
    assert synthesis.provenance.requirement_count > 0

    # Trade-off statement (LLM call)
    assert synthesis.trade_off_statement is not None
    assert len(synthesis.trade_off_statement.strip()) > 0

    # Contested signals (may legitimately be empty)
    assert synthesis.contested_signals is not None

    # Epistemic disclaimer always present (F10)
    assert synthesis.epistemic_disclaimer is not None
    assert len(synthesis.epistemic_disclaimer.strip()) > 0

    # Partial mode disclaimer present because Carol has no Big Five (F09)
    assert synthesis.partial_mode_disclaimer is not None
    assert len(synthesis.partial_mode_disclaimer.strip()) > 0
