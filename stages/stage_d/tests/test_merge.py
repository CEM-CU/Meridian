"""Tests for D3: Merge personality and CV flag streams."""

from __future__ import annotations

from shared.models import (
    EvidenceType,
    Flag,
    FlagCategory,
    Valence,
)
from stage_d.merge import merge_all_candidates, merge_flag_streams

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_personality_flag(
    name: str = "EXECUTION_CONSCIENTIOUSNESS_FIT",
    candidate_name: str = "Alice",
) -> Flag:
    """Build a minimal personality-derived Flag (evidence_type=scored_flag)."""
    return Flag(
        name=name,
        candidate_name=candidate_name,
        category=FlagCategory.EXECUTION,
        valence=Valence.POSITIVE,
        evidence_type=EvidenceType.SCORED_FLAG,
        big_five_source="C",
        big_five_score=0.8,
        threshold_used=0.7,
        topic_keywords=["execution", "conscientiousness"],
        metadata={"scenario": "digital_transformation", "direction": "above"},
    )


def _make_cv_flag(
    name: str = "CV_GAP",
    candidate_name: str = "Alice",
) -> Flag:
    """Build a minimal CV-derived Flag (evidence_type=cv_rubric)."""
    return Flag(
        name=name,
        candidate_name=candidate_name,
        category=FlagCategory.EXPERIENCE_GAP,
        valence=Valence.NEGATIVE,
        evidence_type=EvidenceType.CV_RUBRIC,
        requirement_id="REQ-01",
        rubric_level="gap",
        metadata={"active_priority": "high"},
    )


def _make_requirement_gap_flag(
    name: str = "CV_PARTIAL",
    candidate_name: str = "Alice",
) -> Flag:
    """Build a CV flag with evidence_type=requirement_gap."""
    return Flag(
        name=name,
        candidate_name=candidate_name,
        category=FlagCategory.EXPERIENCE_GAP,
        valence=Valence.NEGATIVE,
        evidence_type=EvidenceType.REQUIREMENT_GAP,
        requirement_id="REQ-02",
        rubric_level="partial",
        metadata={"active_priority": "medium"},
    )


# ---------------------------------------------------------------------------
# merge_flag_streams — single-candidate
# ---------------------------------------------------------------------------


class TestMergeFlagStreams:
    """Tests for the single-candidate merge_flag_streams function."""

    def test_personality_first_then_cv(self) -> None:
        """Personality flags must appear before CV flags in the output."""
        p1 = _make_personality_flag("EXECUTION_CONSCIENTIOUSNESS_FIT")
        p2 = _make_personality_flag("DERAILMENT_NEUROTICISM_UNDER_STRESS")
        c1 = _make_cv_flag("CV_GAP")
        c2 = _make_cv_flag("CV_PARTIAL")

        result = merge_flag_streams([p1, p2], [c1, c2])

        assert result == [p1, p2, c1, c2]

    def test_no_deduplication(self) -> None:
        """Same flag name in both streams must produce two entries in the output."""
        # Use a flag name that could plausibly appear in both streams.
        p = _make_personality_flag("EXECUTION_CONSCIENTIOUSNESS_FIT")
        c = _make_cv_flag("CV_GAP")
        # Give both the same name to prove no dedup occurs.
        p2 = _make_personality_flag("CV_GAP")

        result = merge_flag_streams([p, p2], [c])

        # Both flags with name "CV_GAP" must appear.
        names = [f.name for f in result]
        assert names.count("CV_GAP") == 2
        assert len(result) == 3

    def test_partial_mode_cv_only(self) -> None:
        """Empty personality list (partial mode) → output equals CV flags only."""
        c1 = _make_cv_flag("CV_GAP")
        c2 = _make_cv_flag("CV_PARTIAL")

        result = merge_flag_streams([], [c1, c2])

        assert result == [c1, c2]

    def test_full_mode_both_streams(self) -> None:
        """Non-empty both streams → correct concatenation."""
        p1 = _make_personality_flag("EXECUTION_CONSCIENTIOUSNESS_FIT")
        c1 = _make_cv_flag("CV_GAP")

        result = merge_flag_streams([p1], [c1])

        assert result == [p1, c1]

    def test_empty_both_streams(self) -> None:
        """Both empty lists → empty output."""
        result = merge_flag_streams([], [])

        assert result == []

    def test_inputs_not_mutated(self) -> None:
        """Original personality and CV lists must remain unchanged after merge."""
        p1 = _make_personality_flag("EXECUTION_CONSCIENTIOUSNESS_FIT")
        c1 = _make_cv_flag("CV_GAP")
        personality = [p1]
        cv = [c1]
        original_personality_id = id(personality)
        original_cv_id = id(cv)

        result = merge_flag_streams(personality, cv)

        # Lists must not be the same object as the result.
        assert id(result) != original_personality_id
        assert id(result) != original_cv_id
        # Original lists must still contain only their original elements.
        assert personality == [p1]
        assert cv == [c1]

    def test_flag_count_equals_sum(self) -> None:
        """len(output) must always equal len(personality) + len(cv)."""
        p_flags = [_make_personality_flag(f"PERSONALITY_{i}") for i in range(4)]
        c_flags = [_make_cv_flag("CV_GAP") for _ in range(6)]

        result = merge_flag_streams(p_flags, c_flags)

        assert len(result) == len(p_flags) + len(c_flags)

    def test_evidence_type_ordering(self) -> None:
        """All scored_flag evidence types must precede cv_rubric/requirement_gap types."""
        p1 = _make_personality_flag("EXECUTION_CONSCIENTIOUSNESS_FIT")
        p2 = _make_personality_flag("DERAILMENT_NEUROTICISM_UNDER_STRESS")
        c1 = _make_cv_flag("CV_GAP")
        c2 = _make_requirement_gap_flag("CV_PARTIAL")

        result = merge_flag_streams([p1, p2], [c1, c2])

        scored_indices = [i for i, f in enumerate(result) if f.evidence_type == EvidenceType.SCORED_FLAG]
        cv_indices = [
            i for i, f in enumerate(result) if f.evidence_type in {EvidenceType.CV_RUBRIC, EvidenceType.REQUIREMENT_GAP}
        ]

        # Every scored_flag index must be less than every CV index.
        for si in scored_indices:
            for ci in cv_indices:
                assert si < ci, f"scored_flag at index {si} is after CV flag at index {ci}"

    def test_personality_only_no_cv(self) -> None:
        """Personality flags with empty CV list → output equals personality flags only."""
        p1 = _make_personality_flag("EXECUTION_CONSCIENTIOUSNESS_FIT")
        p2 = _make_personality_flag("DERAILMENT_NEUROTICISM_UNDER_STRESS")

        result = merge_flag_streams([p1, p2], [])

        assert result == [p1, p2]

    def test_returns_new_list_object(self) -> None:
        """merge_flag_streams must return a new list, not a reference to either input."""
        p1 = _make_personality_flag()
        c1 = _make_cv_flag()
        personality = [p1]
        cv = [c1]

        result = merge_flag_streams(personality, cv)

        assert result is not personality
        assert result is not cv


# ---------------------------------------------------------------------------
# merge_all_candidates — batch
# ---------------------------------------------------------------------------


class TestMergeAllCandidates:
    """Tests for the batch merge_all_candidates function."""

    def test_batch_merge_all_candidates(self) -> None:
        """Three candidates with different modes produce correct per-candidate merges."""
        # Alice: full mode (personality + CV)
        alice_p = _make_personality_flag(candidate_name="Alice")
        alice_c = _make_cv_flag(candidate_name="Alice")
        # Bob: partial mode (CV only)
        bob_c = _make_cv_flag(candidate_name="Bob")
        # Carol: personality only (no CV)
        carol_p = _make_personality_flag(candidate_name="Carol")

        personality = {"Alice": [alice_p], "Carol": [carol_p]}
        cv = {"Alice": [alice_c], "Bob": [bob_c]}

        result = merge_all_candidates(personality, cv)

        assert set(result.keys()) == {"Alice", "Bob", "Carol"}
        assert result["Alice"] == [alice_p, alice_c]
        assert result["Bob"] == [bob_c]
        assert result["Carol"] == [carol_p]

    def test_batch_candidate_in_cv_only(self) -> None:
        """Candidate with CV flags but no personality entry gets CV flags only."""
        c1 = _make_cv_flag(candidate_name="Dave")

        result = merge_all_candidates({}, {"Dave": [c1]})

        assert result == {"Dave": [c1]}

    def test_batch_candidate_in_personality_only(self) -> None:
        """Candidate with personality flags but no CV entry gets personality flags only."""
        p1 = _make_personality_flag(candidate_name="Eve")

        result = merge_all_candidates({"Eve": [p1]}, {})

        assert result == {"Eve": [p1]}

    def test_batch_empty_dicts(self) -> None:
        """Both empty dicts → empty result dict."""
        result = merge_all_candidates({}, {})

        assert result == {}

    def test_batch_flag_count_equals_sum_per_candidate(self) -> None:
        """For each candidate, merged count == personality count + cv count."""
        alice_p = [_make_personality_flag(candidate_name="Alice") for _ in range(3)]
        alice_c = [_make_cv_flag(candidate_name="Alice") for _ in range(5)]
        bob_c = [_make_cv_flag(candidate_name="Bob") for _ in range(4)]

        result = merge_all_candidates({"Alice": alice_p}, {"Alice": alice_c, "Bob": bob_c})

        assert len(result["Alice"]) == 3 + 5
        assert len(result["Bob"]) == 4

    def test_batch_personality_first_per_candidate(self) -> None:
        """Personality flags come before CV flags for each candidate in batch merge."""
        p1 = _make_personality_flag("EXECUTION_CONSCIENTIOUSNESS_FIT", "Alice")
        p2 = _make_personality_flag("DERAILMENT_NEUROTICISM_UNDER_STRESS", "Alice")
        c1 = _make_cv_flag("CV_GAP", "Alice")
        c2 = _make_cv_flag("CV_PARTIAL", "Alice")

        result = merge_all_candidates({"Alice": [p1, p2]}, {"Alice": [c1, c2]})

        assert result["Alice"] == [p1, p2, c1, c2]

    def test_batch_inputs_not_mutated(self) -> None:
        """Input dicts and their flag lists must not be mutated by batch merge."""
        p1 = _make_personality_flag(candidate_name="Alice")
        c1 = _make_cv_flag(candidate_name="Alice")
        personality = {"Alice": [p1]}
        cv = {"Alice": [c1]}

        merge_all_candidates(personality, cv)

        assert personality == {"Alice": [p1]}
        assert cv == {"Alice": [c1]}

    def test_batch_all_candidates_in_union(self) -> None:
        """Result contains all candidates that appear in either input dict."""
        p_flags: dict[str, list[Flag]] = {
            "Alice": [_make_personality_flag(candidate_name="Alice")],
            "Bob": [_make_personality_flag(candidate_name="Bob")],
        }
        cv_flags: dict[str, list[Flag]] = {
            "Bob": [_make_cv_flag(candidate_name="Bob")],
            "Carol": [_make_cv_flag(candidate_name="Carol")],
        }

        result = merge_all_candidates(p_flags, cv_flags)

        assert set(result.keys()) == {"Alice", "Bob", "Carol"}
