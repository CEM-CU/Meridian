"""Tests for Stage E Layer 3 Audit — 8 deterministic checks (E5).

Each check is tested independently with crafted inputs. The runner test
exercises the full pipeline.
"""

from __future__ import annotations

from shared.models.candidates import BigFiveScores, CandidateData
from shared.models.flags import EvidenceType, Flag, FlagCategory, Valence
from shared.models.requirements import Priority, Requirement, ScenarioPriority
from shared.models.rubric import Confidence, RubricAssessment, RubricLevel
from stage_e.layer3_audit.checks import (
    check_biographical_references,
    check_downweight_ratio,
    check_flag_scope,
    check_hallucinated_references,
    check_research_general_cap,
    check_schema_validity,
    check_semantic_drift,
    check_unaddressed_flags,
)
from stage_e.layer3_audit.runner import run_audit
from stage_e.schemas import AgentEvidenceType, AgentVerdict, Claim, EvidenceBasis

# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def _make_scenario_priority(default: Priority = Priority.MEDIUM) -> ScenarioPriority:
    """Return a ScenarioPriority with all scenarios set to the same value."""
    return ScenarioPriority(
        digital_transformation=default,
        post_acquisition=default,
        turnaround=default,
        stabilization=default,
        growth=default,
    )


def _make_requirement(
    req_id: str = "REQ-01",
    text: str = "Leadership and team management experience required",
) -> Requirement:
    """Return a Requirement with sensible defaults."""
    return Requirement(
        requirement_id=req_id,
        text=text,
        source_quote=text,
        assessable_from_cv=True,
        scenario_priority=_make_scenario_priority(),
    )


def _make_flag(
    name: str = "EXECUTION_CONSCIENTIOUSNESS_FIT",
    candidate_name: str = "Alice",
    category: FlagCategory = FlagCategory.EXECUTION,
    valence: Valence = Valence.POSITIVE,
    evidence_type: EvidenceType = EvidenceType.SCORED_FLAG,
    requirement_id: str | None = None,
    rubric_level: str | None = None,
    topic_keywords: list[str] | None = None,
    big_five_source: str | None = "C",
) -> Flag:
    """Return a Flag with sensible defaults."""
    return Flag(
        name=name,
        candidate_name=candidate_name,
        category=category,
        valence=valence,
        evidence_type=evidence_type,
        requirement_id=requirement_id,
        rubric_level=rubric_level,
        topic_keywords=topic_keywords or ["leadership", "execution", "management"],
        big_five_source=big_five_source,
    )


def _make_cv_flag(
    name: str = "CV_EXCEEDS",
    candidate_name: str = "Alice",
    category: FlagCategory = FlagCategory.EXPERIENCE_STRENGTH,
    valence: Valence = Valence.POSITIVE,
    requirement_id: str = "REQ-01",
    rubric_level: str = "exceeds",
    topic_keywords: list[str] | None = None,
) -> Flag:
    """Return a CV-derived Flag."""
    return Flag(
        name=name,
        candidate_name=candidate_name,
        category=category,
        valence=valence,
        evidence_type=EvidenceType.CV_RUBRIC,
        requirement_id=requirement_id,
        rubric_level=rubric_level,
        topic_keywords=topic_keywords or ["leadership", "management", "team"],
        big_five_source=None,
    )


def _make_rubric_assessment(
    requirement_id: str = "REQ-01",
    candidate_name: str = "Alice",
    rubric_level: RubricLevel = RubricLevel.MEETS,
    confidence: Confidence = Confidence.HIGH,
    cv_citation: str | None = None,
) -> RubricAssessment:
    """Return a RubricAssessment."""
    return RubricAssessment(
        requirement_id=requirement_id,
        candidate_name=candidate_name,
        rubric_level=rubric_level,
        confidence=confidence,
        cv_citation=cv_citation,
    )


def _make_candidate(
    name: str = "Alice",
    cv_text: str = "Alice has 10 years of leadership experience managing large teams.",
) -> CandidateData:
    """Return a CandidateData with minimal Big Five."""
    return CandidateData(
        name=name,
        cv_text=cv_text,
        big_five=BigFiveScores(O=0.7, C=0.8, E=0.6, A=0.5, N=0.3),
    )


def _make_evidence_basis(
    type: str = "scored_flag",
    reference: str = "EXECUTION_CONSCIENTIOUSNESS_FIT",
    detail: str | None = None,
) -> EvidenceBasis:
    """Return an EvidenceBasis."""
    return EvidenceBasis(type=AgentEvidenceType(type), reference=reference, detail=detail)


def _make_claim(
    text: str = "Alice demonstrates strong execution capabilities relevant to the CTO role",
    evidence_type: str = "scored_flag",
    reference: str = "EXECUTION_CONSCIENTIOUSNESS_FIT",
    confidence: str = "high",
    candidate_name: str = "Alice",
    detail: str | None = None,
) -> Claim:
    """Return a Claim with sensible defaults."""
    return Claim(
        text=text,
        evidence_basis=EvidenceBasis(
            type=AgentEvidenceType(evidence_type),
            reference=reference,
            detail=detail,
        ),
        confidence=confidence,
        candidate_name=candidate_name,
    )


def _make_verdict(
    agent_role: str = "role_fit",
    claims: list[Claim] | None = None,
    summary: str = "Overall role-fit assessment shows strong alignment with requirements.",
    assessment_mode: str = "full",
    unaddressed_flags: list[str] | None = None,
) -> AgentVerdict:
    """Return a valid AgentVerdict."""
    if claims is None:
        claims = [_make_claim()]
    return AgentVerdict(
        agent_role=agent_role,
        claims=claims,
        summary=summary,
        assessment_mode=assessment_mode,
        unaddressed_flags=unaddressed_flags or [],
    )


# ---------------------------------------------------------------------------
# Check 1: JSON Schema Validation
# ---------------------------------------------------------------------------


class TestCheckSchemaValidity:
    """Check 1: schema re-validation."""

    def test_valid_verdict_no_warnings(self) -> None:
        verdict = _make_verdict()
        warnings = check_schema_validity(verdict)
        assert warnings == []

    def test_valid_verdict_with_multiple_claims(self) -> None:
        claims = [_make_claim(text=f"Alice demonstrates competency number {i + 1} for the CTO role") for i in range(3)]
        verdict = _make_verdict(claims=claims)
        warnings = check_schema_validity(verdict)
        assert warnings == []


# ---------------------------------------------------------------------------
# Check 2: Flag Scope Enforcement
# ---------------------------------------------------------------------------


class TestCheckFlagScope:
    """Check 2: agent only cites flags from its allowlist."""

    def test_in_allowlist_claim_kept(self) -> None:
        allowlist = frozenset({FlagCategory.EXECUTION})
        flag = _make_flag(name="EXECUTION_CONSCIENTIOUSNESS_FIT", category=FlagCategory.EXECUTION)
        claim = _make_claim(
            reference="EXECUTION_CONSCIENTIOUSNESS_FIT",
            evidence_type="scored_flag",
        )
        verdict = _make_verdict(claims=[claim])

        new_verdict, warnings = check_flag_scope(verdict, allowlist, [flag])

        assert len(new_verdict.claims) == 1
        assert warnings == []

    def test_out_of_allowlist_claim_stripped(self) -> None:
        allowlist = frozenset({FlagCategory.EXECUTION})
        # Flag is in DERAILMENT, not in allowlist
        flag = _make_flag(
            name="DERAILMENT_NEUROTICISM_UNDER_STRESS",
            category=FlagCategory.DERAILMENT,
        )
        claim = _make_claim(
            reference="DERAILMENT_NEUROTICISM_UNDER_STRESS",
            evidence_type="scored_flag",
        )
        verdict = _make_verdict(claims=[claim])

        new_verdict, warnings = check_flag_scope(verdict, allowlist, [flag])

        assert len(new_verdict.claims) == 0
        assert len(warnings) == 1
        assert "[CHECK2]" in warnings[0]
        assert "DERAILMENT_NEUROTICISM_UNDER_STRESS" in warnings[0]

    def test_non_scored_flag_claim_passes_regardless_of_allowlist(self) -> None:
        """cv_rubric claims are not scope-checked against the flag allowlist."""
        allowlist = frozenset({FlagCategory.EXECUTION})
        claim = _make_claim(
            reference="REQ-01",
            evidence_type="cv_rubric",
        )
        verdict = _make_verdict(claims=[claim])

        new_verdict, warnings = check_flag_scope(verdict, allowlist, [])

        assert len(new_verdict.claims) == 1
        assert warnings == []

    def test_multiple_claims_partial_stripping(self) -> None:
        allowlist = frozenset({FlagCategory.EXECUTION})
        exec_flag = _make_flag(name="EXECUTION_CONSCIENTIOUSNESS_FIT", category=FlagCategory.EXECUTION)
        risk_flag = _make_flag(name="DERAILMENT_NEUROTICISM_UNDER_STRESS", category=FlagCategory.DERAILMENT)
        claims = [
            _make_claim(reference="EXECUTION_CONSCIENTIOUSNESS_FIT", evidence_type="scored_flag"),
            _make_claim(
                text="Alice shows derailment risk under stress conditions on the job",
                reference="DERAILMENT_NEUROTICISM_UNDER_STRESS",
                evidence_type="scored_flag",
            ),
        ]
        verdict = _make_verdict(claims=claims)

        new_verdict, warnings = check_flag_scope(verdict, allowlist, [exec_flag, risk_flag])

        assert len(new_verdict.claims) == 1
        assert len(warnings) == 1

    def test_flag_not_in_available_flags_kept(self) -> None:
        """A scored_flag reference that doesn't match any available flag is kept (Check 4 will catch it)."""
        allowlist = frozenset({FlagCategory.EXECUTION})
        claim = _make_claim(reference="UNKNOWN_FLAG", evidence_type="scored_flag")
        verdict = _make_verdict(claims=[claim])

        new_verdict, warnings = check_flag_scope(verdict, allowlist, [])

        assert len(new_verdict.claims) == 1
        assert warnings == []


# ---------------------------------------------------------------------------
# Check 3: Unaddressed Flag Detection
# ---------------------------------------------------------------------------


class TestCheckUnaddressedFlags:
    """Check 3: flags in allowlist that agent silently dropped."""

    def test_all_flags_cited_no_warnings(self) -> None:
        flag = _make_flag(name="EXECUTION_CONSCIENTIOUSNESS_FIT")
        claim = _make_claim(reference="EXECUTION_CONSCIENTIOUSNESS_FIT", evidence_type="scored_flag")
        verdict = _make_verdict(claims=[claim])

        warnings = check_unaddressed_flags(verdict, [flag])
        assert warnings == []

    def test_uncited_flags_generate_warnings(self) -> None:
        flags = [
            _make_flag(name="EXECUTION_CONSCIENTIOUSNESS_FIT", candidate_name="Alice"),
            _make_flag(name="STRATEGIC_OPENNESS_FIT", candidate_name="Alice"),
            _make_flag(name="CULTURAL_EXTRAVERSION_FIT", candidate_name="Alice"),
            _make_flag(name="EXECUTION_LOW_CONSCIENTIOUSNESS_RISK", candidate_name="Alice"),
            _make_flag(name="STRATEGIC_LOW_OPENNESS_RISK", candidate_name="Alice"),
        ]
        # Only 3 of 5 cited
        claims = [
            _make_claim(
                text=f"Alice demonstrates competency for claim {i + 1} in the CTO role",
                reference=flags[i].name,
                evidence_type="scored_flag",
            )
            for i in range(3)
        ]
        verdict = _make_verdict(claims=claims)

        warnings = check_unaddressed_flags(verdict, flags)

        assert len(warnings) == 2
        assert all("[CHECK3]" in w for w in warnings)

    def test_five_flags_all_cited_no_warnings(self) -> None:
        flags = [
            _make_flag(name="EXECUTION_CONSCIENTIOUSNESS_FIT", candidate_name="Alice"),
            _make_flag(name="STRATEGIC_OPENNESS_FIT", candidate_name="Alice"),
            _make_flag(name="CULTURAL_EXTRAVERSION_FIT", candidate_name="Alice"),
            _make_flag(name="EXECUTION_LOW_CONSCIENTIOUSNESS_RISK", candidate_name="Alice"),
            _make_flag(name="STRATEGIC_LOW_OPENNESS_RISK", candidate_name="Alice"),
        ]
        claims = [
            _make_claim(
                text=f"Alice demonstrates relevant flag {i + 1} for the CTO role",
                reference=flags[i].name,
                evidence_type="scored_flag",
            )
            for i in range(5)
        ]
        verdict = _make_verdict(claims=claims)

        warnings = check_unaddressed_flags(verdict, flags)
        assert warnings == []

    def test_no_flags_no_warnings(self) -> None:
        verdict = _make_verdict()
        warnings = check_unaddressed_flags(verdict, [])
        assert warnings == []


# ---------------------------------------------------------------------------
# Check 4: Hallucinated Flag / Reference Detection
# ---------------------------------------------------------------------------


class TestCheckHallucinatedReferences:
    """Check 4: cited references must exist in canonical vocabulary."""

    def test_valid_flag_name_kept(self) -> None:
        claim = _make_claim(reference="EXECUTION_CONSCIENTIOUSNESS_FIT", evidence_type="scored_flag")
        verdict = _make_verdict(claims=[claim])
        valid_flags = frozenset({"EXECUTION_CONSCIENTIOUSNESS_FIT"})
        valid_reqs = frozenset({"REQ-01"})

        new_verdict, warnings = check_hallucinated_references(verdict, valid_flags, valid_reqs)

        assert len(new_verdict.claims) == 1
        assert warnings == []

    def test_hallucinated_flag_name_stripped(self) -> None:
        claim = _make_claim(reference="INVENTED_FLAG_NAME", evidence_type="scored_flag")
        verdict = _make_verdict(claims=[claim])
        valid_flags = frozenset({"EXECUTION_CONSCIENTIOUSNESS_FIT"})
        valid_reqs = frozenset({"REQ-01"})

        new_verdict, warnings = check_hallucinated_references(verdict, valid_flags, valid_reqs)

        assert len(new_verdict.claims) == 0
        assert len(warnings) == 1
        assert "[CHECK4]" in warnings[0]
        assert "INVENTED_FLAG_NAME" in warnings[0]

    def test_valid_requirement_id_kept(self) -> None:
        claim = _make_claim(reference="REQ-01", evidence_type="cv_rubric")
        verdict = _make_verdict(claims=[claim])
        valid_flags = frozenset({"EXECUTION_CONSCIENTIOUSNESS_FIT"})
        valid_reqs = frozenset({"REQ-01"})

        new_verdict, warnings = check_hallucinated_references(verdict, valid_flags, valid_reqs)

        assert len(new_verdict.claims) == 1
        assert warnings == []

    def test_hallucinated_requirement_id_stripped(self) -> None:
        """REQ-17 when confirmed list only goes to REQ-12 — hallucinated reference."""
        claim = _make_claim(reference="REQ-17", evidence_type="cv_rubric")
        verdict = _make_verdict(claims=[claim])
        valid_flags = frozenset({"EXECUTION_CONSCIENTIOUSNESS_FIT"})
        valid_reqs = frozenset({f"REQ-{i:02d}" for i in range(1, 13)})  # REQ-01 to REQ-12

        new_verdict, warnings = check_hallucinated_references(verdict, valid_flags, valid_reqs)

        assert len(new_verdict.claims) == 0
        assert len(warnings) == 1
        assert "REQ-17" in warnings[0]

    def test_invalid_requirement_gap_reference_stripped(self) -> None:
        claim = _make_claim(reference="REQ-99", evidence_type="requirement_gap")
        verdict = _make_verdict(claims=[claim])
        valid_flags = frozenset()
        valid_reqs = frozenset({"REQ-01"})

        new_verdict, warnings = check_hallucinated_references(verdict, valid_flags, valid_reqs)

        assert len(new_verdict.claims) == 0
        assert len(warnings) == 1

    def test_biographical_pattern_not_checked(self) -> None:
        """biographical_pattern references are not validated in Check 4."""
        claim = _make_claim(
            text="Alice shows consistent career progression pattern toward larger organisations",
            reference="any_free_text_reference_here",
            evidence_type="biographical_pattern",
        )
        verdict = _make_verdict(claims=[claim])

        new_verdict, warnings = check_hallucinated_references(verdict, frozenset(), frozenset())

        assert len(new_verdict.claims) == 1
        assert warnings == []


# ---------------------------------------------------------------------------
# Check 5 (F04): Biographical Reference Validation
# ---------------------------------------------------------------------------


class TestCheckBiographicalReferences:
    """Check 5 (F04): cv_rubric and requirement_gap claims validated against rubric matrix."""

    def test_valid_cv_rubric_claim_kept(self) -> None:
        rubric = _make_rubric_assessment(
            requirement_id="REQ-01",
            candidate_name="Alice",
            rubric_level=RubricLevel.MEETS,
        )
        claim = _make_claim(
            reference="REQ-01",
            evidence_type="cv_rubric",
            candidate_name="Alice",
        )
        verdict = _make_verdict(claims=[claim])
        candidate = _make_candidate()
        requirements = [_make_requirement("REQ-01")]

        new_verdict, warnings = check_biographical_references(verdict, [candidate], [rubric], requirements)

        assert len(new_verdict.claims) == 1
        assert warnings == []

    def test_cv_rubric_invalid_requirement_id_stripped(self) -> None:
        claim = _make_claim(
            reference="REQ-99",
            evidence_type="cv_rubric",
            candidate_name="Alice",
        )
        verdict = _make_verdict(claims=[claim])
        candidate = _make_candidate()

        new_verdict, warnings = check_biographical_references(verdict, [candidate], [], [])

        assert len(new_verdict.claims) == 0
        assert len(warnings) == 1
        assert "[CHECK5]" in warnings[0]

    def test_cv_rubric_fabricated_passage_stripped(self) -> None:
        """Agent cites a passage that does not appear in the actual CV text."""
        rubric = _make_rubric_assessment(
            requirement_id="REQ-01",
            candidate_name="Alice",
            rubric_level=RubricLevel.MEETS,
            cv_citation="managed $80M budget at Siemens",
        )
        # Agent fabricated an inflated figure in detail field
        claim = _make_claim(
            text="Alice managed a large P&L at Siemens demonstrating financial leadership",
            reference="REQ-01",
            evidence_type="cv_rubric",
            candidate_name="Alice",
            detail="managed $800M budget at Siemens",  # fabricated — not in CV
        )
        verdict = _make_verdict(claims=[claim])
        candidate = _make_candidate(
            name="Alice",
            cv_text="Alice managed $80M budget at Siemens during her tenure as VP Finance.",
        )
        requirements = [_make_requirement("REQ-01")]

        new_verdict, warnings = check_biographical_references(verdict, [candidate], [rubric], requirements)

        assert len(new_verdict.claims) == 0
        assert len(warnings) == 1
        assert "[CHECK5]" in warnings[0]

    def test_cv_rubric_correct_passage_kept(self) -> None:
        """Agent cites a passage that is actually present in the CV text."""
        rubric = _make_rubric_assessment(
            requirement_id="REQ-01",
            candidate_name="Alice",
            rubric_level=RubricLevel.MEETS,
        )
        claim = _make_claim(
            text="Alice managed a team at Siemens demonstrating relevant leadership experience",
            reference="REQ-01",
            evidence_type="cv_rubric",
            candidate_name="Alice",
            detail="managed $80M budget at siemens",  # normalised match should work
        )
        verdict = _make_verdict(claims=[claim])
        candidate = _make_candidate(
            name="Alice",
            cv_text="Alice managed $80M budget at Siemens during her tenure as VP Finance.",
        )
        requirements = [_make_requirement("REQ-01")]

        new_verdict, warnings = check_biographical_references(verdict, [candidate], [rubric], requirements)

        assert len(new_verdict.claims) == 1
        assert warnings == []

    def test_requirement_gap_valid_gap_level_kept(self) -> None:
        rubric = _make_rubric_assessment(
            requirement_id="REQ-02",
            candidate_name="Alice",
            rubric_level=RubricLevel.GAP,
        )
        claim = _make_claim(
            text="Alice has no evidence of EMEA operations experience in her background",
            reference="REQ-02",
            evidence_type="requirement_gap",
            candidate_name="Alice",
        )
        verdict = _make_verdict(claims=[claim])
        candidate = _make_candidate()
        requirements = [_make_requirement("REQ-02")]

        new_verdict, warnings = check_biographical_references(verdict, [candidate], [rubric], requirements)

        assert len(new_verdict.claims) == 1
        assert warnings == []

    def test_requirement_gap_not_assessable_kept(self) -> None:
        rubric = _make_rubric_assessment(
            requirement_id="REQ-02",
            candidate_name="Alice",
            rubric_level=RubricLevel.NOT_ASSESSABLE,
        )
        claim = _make_claim(
            text="Alice has insufficient evidence of EMEA operations leadership in her CV",
            reference="REQ-02",
            evidence_type="requirement_gap",
            candidate_name="Alice",
        )
        verdict = _make_verdict(claims=[claim])
        candidate = _make_candidate()
        requirements = [_make_requirement("REQ-02")]

        new_verdict, warnings = check_biographical_references(verdict, [candidate], [rubric], requirements)

        assert len(new_verdict.claims) == 1
        assert warnings == []

    def test_requirement_gap_rubric_says_meets_caught(self) -> None:
        """Agent claims gap but rubric says MEETS — misrepresentation of evidence."""
        rubric = _make_rubric_assessment(
            requirement_id="REQ-01",
            candidate_name="Alice",
            rubric_level=RubricLevel.MEETS,  # NOT a gap!
        )
        claim = _make_claim(
            text="Alice has no evidence of leadership experience in her professional background",
            reference="REQ-01",
            evidence_type="requirement_gap",
            candidate_name="Alice",
        )
        verdict = _make_verdict(claims=[claim])
        candidate = _make_candidate()
        requirements = [_make_requirement("REQ-01")]

        new_verdict, warnings = check_biographical_references(verdict, [candidate], [rubric], requirements)

        assert len(new_verdict.claims) == 0
        assert len(warnings) == 1
        assert "[CHECK5]" in warnings[0]
        assert "misrepresentation" in warnings[0]

    def test_requirement_gap_rubric_says_partial_caught(self) -> None:
        """PARTIAL is not a gap — agent overclaims the absence of evidence."""
        rubric = _make_rubric_assessment(
            requirement_id="REQ-01",
            candidate_name="Alice",
            rubric_level=RubricLevel.PARTIAL,
        )
        claim = _make_claim(
            text="Alice shows no evidence of the required leadership skills in her CV",
            reference="REQ-01",
            evidence_type="requirement_gap",
            candidate_name="Alice",
        )
        verdict = _make_verdict(claims=[claim])
        candidate = _make_candidate()
        requirements = [_make_requirement("REQ-01")]

        new_verdict, warnings = check_biographical_references(verdict, [candidate], [rubric], requirements)

        assert len(new_verdict.claims) == 0
        assert len(warnings) == 1


# ---------------------------------------------------------------------------
# Check 6 (F05): Semantic Drift Detection
# ---------------------------------------------------------------------------


class TestCheckSemanticDrift:
    """Check 6 (F05): keyword overlap between claim text and flag topic_keywords."""

    def test_high_keyword_overlap_no_warning(self) -> None:
        flag = _make_flag(
            name="EXECUTION_CONSCIENTIOUSNESS_FIT",
            topic_keywords=["execution", "leadership", "management", "team", "delivery"],
        )
        claim = _make_claim(
            text="Alice demonstrates strong execution and leadership in team management and delivery",
            reference="EXECUTION_CONSCIENTIOUSNESS_FIT",
            evidence_type="scored_flag",
        )
        verdict = _make_verdict(claims=[claim])

        warnings = check_semantic_drift(verdict, [flag])
        assert warnings == []

    def test_low_keyword_overlap_drift_warning(self) -> None:
        flag = _make_flag(
            name="EXECUTION_CONSCIENTIOUSNESS_FIT",
            topic_keywords=["execution", "leadership", "management", "team", "delivery"],
            candidate_name="Alice",
        )
        # Claim text uses unrelated vocabulary — <20% overlap
        claim = _make_claim(
            text="Alice has demonstrated remarkable innovation in financial modelling and risk modelling",
            reference="EXECUTION_CONSCIENTIOUSNESS_FIT",
            evidence_type="scored_flag",
            candidate_name="Alice",
        )
        verdict = _make_verdict(claims=[claim])

        warnings = check_semantic_drift(verdict, [flag])

        assert len(warnings) == 1
        assert "[DRIFT]" in warnings[0]

    def test_drift_does_not_strip_claims(self) -> None:
        """Semantic drift adds a warning but never strips the claim."""
        flag = _make_flag(
            name="EXECUTION_CONSCIENTIOUSNESS_FIT",
            topic_keywords=["execution", "leadership", "management", "team", "delivery"],
            candidate_name="Alice",
        )
        claim = _make_claim(
            text="Alice demonstrates remarkable innovation in financial modelling and capital allocation",
            reference="EXECUTION_CONSCIENTIOUSNESS_FIT",
            evidence_type="scored_flag",
            candidate_name="Alice",
        )
        verdict = _make_verdict(claims=[claim])

        warnings = check_semantic_drift(verdict, [flag])

        assert len(warnings) == 1  # Warning produced
        # Original verdict unchanged (check_semantic_drift doesn't return a new verdict)
        assert len(verdict.claims) == 1

    def test_research_general_evidence_not_checked(self) -> None:
        """research_general claims are not scope-checked for semantic drift."""
        claim = _make_claim(
            text="Research suggests that high conscientiousness candidates perform better in operational roles",
            reference="I/O psychology literature",
            evidence_type="research_general",
        )
        verdict = _make_verdict(claims=[claim])

        warnings = check_semantic_drift(verdict, [])
        assert warnings == []

    def test_cv_rubric_claim_drift_detected(self) -> None:
        """Drift check applies to cv_rubric claims via CV flag topic keywords."""
        cv_flag = _make_cv_flag(
            requirement_id="REQ-01",
            topic_keywords=["leadership", "management", "team", "operations"],
            candidate_name="Alice",
        )
        # Claim talks about personality language while citing CV evidence
        claim = _make_claim(
            text="Alice shows high openness to experience and neuroticism under pressure stress",
            reference="REQ-01",
            evidence_type="cv_rubric",
            candidate_name="Alice",
        )
        verdict = _make_verdict(claims=[claim])

        warnings = check_semantic_drift(verdict, [cv_flag])
        assert len(warnings) == 1
        assert "[DRIFT]" in warnings[0]


# ---------------------------------------------------------------------------
# Check 7 (F07): research_general Cap
# ---------------------------------------------------------------------------


class TestCheckResearchGeneralCap:
    """Check 7 (F07): max 2 research_general claims per agent."""

    def _make_research_verdict(self, count: int) -> AgentVerdict:
        """Build a verdict with count research_general claims."""
        research_claims = [
            _make_claim(
                text=f"Research in I/O psychology indicates that claim number {i + 1} is relevant",
                reference="I/O psychology literature",
                evidence_type="research_general",
            )
            for i in range(count)
        ]
        if not research_claims:
            research_claims = [_make_claim()]
        return _make_verdict(claims=research_claims)

    def test_two_research_general_within_cap(self) -> None:
        verdict = self._make_research_verdict(2)
        warnings = check_research_general_cap(verdict)
        assert warnings == []

    def test_one_research_general_within_cap(self) -> None:
        verdict = self._make_research_verdict(1)
        warnings = check_research_general_cap(verdict)
        assert warnings == []

    def test_three_research_general_exceeds_cap(self) -> None:
        verdict = self._make_research_verdict(3)
        warnings = check_research_general_cap(verdict)
        assert len(warnings) == 1
        assert "[CHECK7]" in warnings[0]
        assert "3" in warnings[0]

    def test_custom_cap_of_one(self) -> None:
        verdict = self._make_research_verdict(2)
        warnings = check_research_general_cap(verdict, cap=1)
        assert len(warnings) == 1


# ---------------------------------------------------------------------------
# Check 8 (F14): Downweight Ratio Warning
# ---------------------------------------------------------------------------


class TestCheckDownweightRatio:
    """Check 8 (F14): warning if agent downweights >50% of in-mandate flags."""

    def test_majority_cited_no_warning(self) -> None:
        """3/5 flags cited — below 50% uncited threshold, no warning."""
        flags = [
            _make_flag(name="EXECUTION_CONSCIENTIOUSNESS_FIT", candidate_name="Alice"),
            _make_flag(name="STRATEGIC_OPENNESS_FIT", candidate_name="Alice"),
            _make_flag(name="CULTURAL_EXTRAVERSION_FIT", candidate_name="Alice"),
            _make_flag(name="EXECUTION_LOW_CONSCIENTIOUSNESS_RISK", candidate_name="Alice"),
            _make_flag(name="STRATEGIC_LOW_OPENNESS_RISK", candidate_name="Alice"),
        ]
        claims = [
            _make_claim(
                text=f"Alice demonstrates flag {i + 1} relevant to CTO execution requirements",
                reference=flags[i].name,
                evidence_type="scored_flag",
                candidate_name="Alice",
            )
            for i in range(3)
        ]
        verdict = _make_verdict(claims=claims)

        warnings = check_downweight_ratio(verdict, flags, threshold=0.5)
        # 3/5 cited = 40% uncited < 50% threshold → no warning
        assert warnings == []

    def test_minority_cited_warning_fires(self) -> None:
        """1/5 flags cited — 80% uncited, exceeds 50% threshold."""
        flags = [
            _make_flag(name="EXECUTION_CONSCIENTIOUSNESS_FIT", candidate_name="Alice"),
            _make_flag(name="STRATEGIC_OPENNESS_FIT", candidate_name="Alice"),
            _make_flag(name="CULTURAL_EXTRAVERSION_FIT", candidate_name="Alice"),
            _make_flag(name="EXECUTION_LOW_CONSCIENTIOUSNESS_RISK", candidate_name="Alice"),
            _make_flag(name="STRATEGIC_LOW_OPENNESS_RISK", candidate_name="Alice"),
        ]
        claims = [
            _make_claim(
                reference="EXECUTION_CONSCIENTIOUSNESS_FIT",
                evidence_type="scored_flag",
                candidate_name="Alice",
            )
        ]
        verdict = _make_verdict(claims=claims)

        warnings = check_downweight_ratio(verdict, flags, threshold=0.5)
        # 1/5 cited = 80% uncited > 50% threshold → warning
        assert len(warnings) == 1
        assert "[CHECK8]" in warnings[0]

    def test_all_flags_cited_no_warning(self) -> None:
        flags = [
            _make_flag(name="EXECUTION_CONSCIENTIOUSNESS_FIT", candidate_name="Alice"),
            _make_flag(name="STRATEGIC_OPENNESS_FIT", candidate_name="Alice"),
        ]
        claims = [
            _make_claim(
                text="Alice demonstrates execution capabilities suitable for the CTO position",
                reference="EXECUTION_CONSCIENTIOUSNESS_FIT",
                evidence_type="scored_flag",
                candidate_name="Alice",
            ),
            _make_claim(
                text="Alice demonstrates strategic thinking capabilities for the CTO role",
                reference="STRATEGIC_OPENNESS_FIT",
                evidence_type="scored_flag",
                candidate_name="Alice",
            ),
        ]
        verdict = _make_verdict(claims=claims)

        warnings = check_downweight_ratio(verdict, flags)
        assert warnings == []

    def test_no_flags_no_warning(self) -> None:
        verdict = _make_verdict()
        warnings = check_downweight_ratio(verdict, [])
        assert warnings == []

    def test_cv_flags_counted_via_requirement_id(self) -> None:
        """CV flags cited via cv_rubric are counted as cited by requirement_id."""
        cv_flag = _make_cv_flag(
            name="CV_EXCEEDS",
            requirement_id="REQ-01",
            candidate_name="Alice",
        )
        claim = _make_claim(
            text="Alice clearly exceeds the leadership requirement per the rubric assessment",
            reference="REQ-01",
            evidence_type="cv_rubric",
            candidate_name="Alice",
        )
        verdict = _make_verdict(claims=[claim])

        warnings = check_downweight_ratio(verdict, [cv_flag], threshold=0.5)
        assert warnings == []


# ---------------------------------------------------------------------------
# Runner: run_audit integration test
# ---------------------------------------------------------------------------


class TestRunAudit:
    """Full audit runner with mixed valid/invalid claims."""

    def test_none_verdict_skipped(self) -> None:
        verdicts: dict[str, AgentVerdict | None] = {
            "role_fit": None,
            "team_dynamics": None,
            "risk": None,
        }
        audited, warnings = run_audit(verdicts, [], [], [], [])

        assert audited == {}
        assert warnings == []

    def test_valid_verdict_passes_cleanly(self) -> None:
        flag = _make_flag(
            name="EXECUTION_CONSCIENTIOUSNESS_FIT",
            category=FlagCategory.EXECUTION,
            candidate_name="Alice",
        )
        claim = _make_claim(
            reference="EXECUTION_CONSCIENTIOUSNESS_FIT",
            evidence_type="scored_flag",
            candidate_name="Alice",
        )
        verdict = _make_verdict(agent_role="role_fit", claims=[claim])
        verdicts: dict[str, AgentVerdict | None] = {"role_fit": verdict}
        requirements = [_make_requirement("REQ-01")]
        candidate = _make_candidate()

        audited, warnings = run_audit(verdicts, [flag], [candidate], [], requirements)

        assert "role_fit" in audited
        # No hallucination warnings (valid flag name)
        hallucination_warnings = [w for w in warnings if "[CHECK4]" in w]
        assert hallucination_warnings == []

    def test_mixed_valid_and_invalid_claims_cleaned(self) -> None:
        """Runner strips invalid claims and returns cleaned verdict."""
        valid_flag = _make_flag(
            name="EXECUTION_CONSCIENTIOUSNESS_FIT",
            category=FlagCategory.EXECUTION,
            candidate_name="Alice",
        )
        valid_claim = _make_claim(
            reference="EXECUTION_CONSCIENTIOUSNESS_FIT",
            evidence_type="scored_flag",
            candidate_name="Alice",
        )
        invalid_claim = _make_claim(
            text="Alice has an unknown flag reference that does not exist in vocabulary",
            reference="HALLUCINATED_FLAG_XYZ",
            evidence_type="scored_flag",
            candidate_name="Alice",
        )
        verdict = _make_verdict(agent_role="role_fit", claims=[valid_claim, invalid_claim])
        verdicts: dict[str, AgentVerdict | None] = {"role_fit": verdict}
        requirements = [_make_requirement("REQ-01")]
        candidate = _make_candidate()

        audited, warnings = run_audit(verdicts, [valid_flag], [candidate], [], requirements)

        assert "role_fit" in audited
        # Hallucinated claim stripped
        assert len(audited["role_fit"].claims) == 1
        assert audited["role_fit"].claims[0].evidence_basis.reference == "EXECUTION_CONSCIENTIOUSNESS_FIT"
        # Warning generated
        check4_warnings = [w for w in warnings if "[CHECK4]" in w]
        assert len(check4_warnings) == 1

    def test_multiple_agents_all_audited(self) -> None:
        """All non-None verdicts get audited."""
        role_fit_verdict = _make_verdict(agent_role="role_fit")
        risk_verdict = _make_verdict(
            agent_role="risk",
            claims=[
                _make_claim(
                    text="Candidate shows derailment risk based on neuroticism score elevated levels",
                    reference="DERAILMENT_NEUROTICISM_UNDER_STRESS",
                    evidence_type="scored_flag",
                    candidate_name="Alice",
                )
            ],
        )
        verdicts: dict[str, AgentVerdict | None] = {
            "role_fit": role_fit_verdict,
            "team_dynamics": None,
            "risk": risk_verdict,
        }
        requirements = [_make_requirement("REQ-01")]
        candidate = _make_candidate()

        audited, _warnings = run_audit(verdicts, [], [candidate], [], requirements)

        assert "role_fit" in audited
        assert "risk" in audited
        assert "team_dynamics" not in audited

    def test_requirement_gap_misrepresentation_caught_by_runner(self) -> None:
        """Full pipeline catches requirement_gap claims where rubric says MEETS."""
        rubric = _make_rubric_assessment(
            requirement_id="REQ-01",
            candidate_name="Alice",
            rubric_level=RubricLevel.MEETS,
        )
        bad_claim = _make_claim(
            text="Alice has no evidence of leadership experience whatsoever in her career history",
            reference="REQ-01",
            evidence_type="requirement_gap",
            candidate_name="Alice",
        )
        good_claim = _make_claim(
            text="Alice demonstrates execution capability meeting the role requirements well",
            reference="EXECUTION_CONSCIENTIOUSNESS_FIT",
            evidence_type="scored_flag",
            candidate_name="Alice",
        )
        verdict = _make_verdict(
            agent_role="risk",
            claims=[bad_claim, good_claim],
        )
        verdicts: dict[str, AgentVerdict | None] = {"risk": verdict}
        requirements = [_make_requirement("REQ-01")]
        candidate = _make_candidate()

        # RISK agent has EXPERIENCE_GAP in its allowlist — use an EXPERIENCE_GAP flag
        exec_flag = _make_flag(
            name="EXECUTION_CONSCIENTIOUSNESS_FIT",
            category=FlagCategory.EXPERIENCE_GAP,
            candidate_name="Alice",
        )

        audited, warnings = run_audit(verdicts, [exec_flag], [candidate], [rubric], requirements)

        check5_warnings = [w for w in warnings if "[CHECK5]" in w]
        assert len(check5_warnings) >= 1
        assert len(audited["risk"].claims) == 1  # bad claim stripped
