"""Tests for D5: assessment mode determination."""

from meridian.derivation.assessment_mode import determine_assessment_mode, determine_modes_batch
from meridian.models.candidates import BigFiveScores, CandidateData
from meridian.models.pipeline import AssessmentMode


def _make_candidate(
    name: str = "Alice",
    big_five: BigFiveScores | None = None,
    personality_source: str | None = None,
) -> CandidateData:
    """Create a minimal CandidateData for testing."""
    return CandidateData(
        name=name,
        cv_text="Sample CV text.",
        big_five=big_five,
        personality_source=personality_source,
    )


def _all_scores() -> BigFiveScores:
    return BigFiveScores(O=0.7, C=0.6, E=0.5, A=0.4, N=0.3)


class TestDetermineAssessmentMode:
    """Tests for determine_assessment_mode."""

    def test_full_mode_with_all_big_five_scores(self) -> None:
        candidate = _make_candidate(big_five=_all_scores(), personality_source="manual")
        mode, _ = determine_assessment_mode(candidate)

        assert mode is AssessmentMode.FULL

    def test_partial_mode_without_big_five(self) -> None:
        candidate = _make_candidate(big_five=None)
        mode, _ = determine_assessment_mode(candidate)

        assert mode is AssessmentMode.PARTIAL

    def test_preset_source_provenance(self) -> None:
        candidate = _make_candidate(
            big_five=_all_scores(),
            personality_source="Preset — Visionary",
        )
        _, provenance = determine_assessment_mode(candidate)

        assert provenance == "Preset archetype — Visionary"

    def test_modified_preset_passthrough(self) -> None:
        source = "Modified preset — based on Visionary with manual adjustments"
        candidate = _make_candidate(
            big_five=_all_scores(),
            personality_source=source,
        )
        _, provenance = determine_assessment_mode(candidate)

        assert provenance == source

    def test_manual_entry_provenance(self) -> None:
        candidate = _make_candidate(
            big_five=_all_scores(),
            personality_source="manual",
        )
        _, provenance = determine_assessment_mode(candidate)

        assert provenance == "Manual Big Five score entry"

    def test_no_source_no_scores_provenance(self) -> None:
        candidate = _make_candidate(big_five=None, personality_source=None)
        _, provenance = determine_assessment_mode(candidate)

        assert provenance == "No personality data provided"

    def test_unknown_source_with_scores(self) -> None:
        candidate = _make_candidate(
            big_five=_all_scores(),
            personality_source=None,
        )
        _, provenance = determine_assessment_mode(candidate)

        assert provenance == "Unknown source"

    def test_custom_source_passthrough(self) -> None:
        candidate = _make_candidate(
            big_five=_all_scores(),
            personality_source="External assessment tool v2",
        )
        _, provenance = determine_assessment_mode(candidate)

        assert provenance == "External assessment tool v2"

    def test_modes_are_valid_enum_values(self) -> None:
        full_candidate = _make_candidate(big_five=_all_scores())
        partial_candidate = _make_candidate(big_five=None)

        mode_full, _ = determine_assessment_mode(full_candidate)
        mode_partial, _ = determine_assessment_mode(partial_candidate)

        assert isinstance(mode_full, AssessmentMode)
        assert isinstance(mode_partial, AssessmentMode)


class TestDetermineModesBatch:
    """Tests for determine_modes_batch."""

    def test_batch_with_mixed_candidates(self) -> None:
        candidates = [
            _make_candidate(name="Full", big_five=_all_scores(), personality_source="manual"),
            _make_candidate(name="Partial", big_five=None, personality_source=None),
            _make_candidate(
                name="Preset",
                big_five=_all_scores(),
                personality_source="Preset — Executor",
            ),
        ]

        result = determine_modes_batch(candidates)

        assert len(result) == 3
        assert result["Full"][0] is AssessmentMode.FULL
        assert result["Partial"][0] is AssessmentMode.PARTIAL
        assert result["Preset"][0] is AssessmentMode.FULL

    def test_batch_provenance_strings(self) -> None:
        candidates = [
            _make_candidate(name="Manual", big_five=_all_scores(), personality_source="manual"),
            _make_candidate(name="None", big_five=None, personality_source=None),
        ]

        result = determine_modes_batch(candidates)

        assert result["Manual"][1] == "Manual Big Five score entry"
        assert result["None"][1] == "No personality data provided"

    def test_batch_empty_list(self) -> None:
        result = determine_modes_batch([])

        assert result == {}
