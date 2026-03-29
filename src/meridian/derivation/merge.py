"""D3: Merge personality and CV flag streams.

Concatenates personality-derived flags (from D1) with validated CV-derived flags
(from D2) into a single ordered list per candidate. Personality flags come first
for deterministic ordering in downstream audit and agent inputs.

No deduplication or conflict resolution — the two streams measure different things
and cross-stream tension is an intentional signal for Stage E synthesis.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from meridian.models import Flag


def merge_flag_streams(
    personality_flags: list[Flag],
    cv_flags: list[Flag],
) -> list[Flag]:
    """Merge personality and CV flag streams for a single candidate.

    Args:
        personality_flags: Flags from D1 (evidence_type=scored_flag).
            Empty list in partial mode (no Big Five scores).
        cv_flags: Validated flags from D2 (evidence_type in
            cv_rubric/requirement_gap/cv_pattern/routing).

    Returns:
        New list with personality flags first, then CV flags. Never mutates inputs.
    """
    return [*personality_flags, *cv_flags]


def merge_all_candidates(
    personality_flags_per_candidate: dict[str, list[Flag]],
    cv_flags_per_candidate: dict[str, list[Flag]],
) -> dict[str, list[Flag]]:
    """Merge flag streams for all candidates.

    Args:
        personality_flags_per_candidate: Candidate name -> personality flags (from D1).
        cv_flags_per_candidate: Candidate name -> validated CV flags (from D2).

    Returns:
        Dict mapping candidate name -> merged flag list.
        Candidates appearing in only one stream get flags from that stream only.
    """
    all_candidates: set[str] = set(personality_flags_per_candidate) | set(cv_flags_per_candidate)

    return {
        candidate: merge_flag_streams(
            personality_flags=personality_flags_per_candidate.get(candidate, []),
            cv_flags=cv_flags_per_candidate.get(candidate, []),
        )
        for candidate in all_candidates
    }
