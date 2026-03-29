"""E2: Layer 1 — Scenario Weight Application, Signal Computation, and Tension Map.

Takes validated flags and the active ScenarioConfig. Produces:
- Weighted scores per candidate
- Signal-strength labels per candidate
- Risk bands per candidate
- Tension map (flag pairs creating interpretive tension)

Zero LLM calls. All computation is deterministic.

CRITICAL (F02): signal_labels and risk_bands in Layer1Output must NOT be passed
to agent inputs. They are reserved for the synthesis template only.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum

from shared.models import EvidenceType, Flag, FlagCategory, ScenarioConfig, Valence

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default category weights
# ---------------------------------------------------------------------------

_DEFAULT_CATEGORY_WEIGHTS: dict[str, float] = {
    "EXECUTION": 1.0,
    "STRATEGIC": 1.0,
    "COLLISION": 0.8,
    "COMPLEMENT": 0.7,
    "FRICTION": 0.8,
    "CULTURAL": 0.7,
    "DERAILMENT": 1.2,
    "DARK_SIDE": 1.3,
    "INTEGRATION": 0.6,
    "TENURE": 0.5,
    "GROUPTHINK": 0.7,
    "EXPERIENCE_STRENGTH": 1.1,
    "EXPERIENCE_GAP": 1.0,
    "EVIDENCE_QUALITY": 0.8,
    "ROUTING": 0.0,
}

# ---------------------------------------------------------------------------
# Risk categories used to compute risk bands
# ---------------------------------------------------------------------------

_RISK_CATEGORIES: frozenset[FlagCategory] = frozenset(
    {
        FlagCategory.DERAILMENT,
        FlagCategory.DARK_SIDE,
        FlagCategory.TENURE,
        FlagCategory.EVIDENCE_QUALITY,
    }
)

# High-priority flag names that count toward risk even in EXPERIENCE_GAP category.
_HIGH_PRIORITY_EXPERIENCE_GAP_NAMES: frozenset[str] = frozenset({"CV_GAP"})

# ---------------------------------------------------------------------------
# Domain-matching lookup tables for tension map
# ---------------------------------------------------------------------------

# CV flag categories → interpretive domain.
_CV_FLAG_DOMAIN: dict[FlagCategory, str] = {
    FlagCategory.EXPERIENCE_STRENGTH: "EXECUTION",
    FlagCategory.EXPERIENCE_GAP: "EXECUTION",
}

# Personality flag categories → interpretive domain.
_PERSONALITY_FLAG_DOMAIN: dict[FlagCategory, str] = {
    FlagCategory.EXECUTION: "EXECUTION",
    FlagCategory.DERAILMENT: "EXECUTION",
    FlagCategory.DARK_SIDE: "EXECUTION",
    FlagCategory.STRATEGIC: "STRATEGIC",
    FlagCategory.CULTURAL: "CULTURAL",
    FlagCategory.FRICTION: "EXECUTION",
    FlagCategory.COLLISION: "EXECUTION",
    FlagCategory.INTEGRATION: "EXECUTION",
    FlagCategory.GROUPTHINK: "STRATEGIC",
    FlagCategory.TENURE: "EXECUTION",
    FlagCategory.COMPLEMENT: "EXECUTION",
}


# ---------------------------------------------------------------------------
# Signal strength and risk band enums
# ---------------------------------------------------------------------------


class SignalStrength(StrEnum):
    """Per-candidate signal strength label computed from weighted flag sums."""

    STRONG_POSITIVE = "strong_positive"
    POSITIVE = "positive"
    MIXED = "mixed"
    NEGATIVE = "negative"
    STRONG_NEGATIVE = "strong_negative"
    INSUFFICIENT_DATA = "insufficient_data"


class RiskBand(StrEnum):
    """Per-candidate risk band computed from risk-category flag counts."""

    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"
    INSUFFICIENT_DATA = "insufficient_data"


# ---------------------------------------------------------------------------
# TensionPair
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TensionPair:
    """A pair of flags creating interpretive tension for a candidate."""

    candidate_name: str
    positive_flag: str
    negative_flag: str
    domain: str
    tension_type: str  # "cross_stream" or "intra_stream"
    description: str


# ---------------------------------------------------------------------------
# Layer1Output
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Layer1Output:
    """Complete Layer 1 computation output.

    CRITICAL (F02): signal_labels and risk_bands must NOT be passed to agent
    inputs. They are reserved for the synthesis template only.
    """

    weighted_scores_per_candidate: dict[str, float]
    signal_labels: dict[str, SignalStrength]
    risk_bands: dict[str, RiskBand]
    tension_map: list[TensionPair]
    partial_mode_notes: list[str]


# ---------------------------------------------------------------------------
# Weight resolution
# ---------------------------------------------------------------------------


def _resolve_weights(scenario: ScenarioConfig) -> dict[str, float]:
    """Merge scenario-specific weights over the defaults.

    Scenario weights override defaults where provided; uncovered categories
    fall back to _DEFAULT_CATEGORY_WEIGHTS.
    """
    merged = dict(_DEFAULT_CATEGORY_WEIGHTS)
    merged.update(scenario.category_weights)
    return merged


def _weight_for_flag(flag: Flag, weights: dict[str, float]) -> float:
    """Return the scenario weight for a flag's category."""
    return weights.get(flag.category.value, 1.0)


# ---------------------------------------------------------------------------
# Weighted score computation
# ---------------------------------------------------------------------------


def _compute_weighted_score(candidate_flags: list[Flag], weights: dict[str, float]) -> float:
    """Sum weighted contributions for one candidate.

    Positive valence flags add their weight; negative valence flags subtract it.
    ROUTING flags always contribute 0 (weight is 0.0 by default).
    NEUTRAL flags contribute 0.
    """
    total = 0.0
    for flag in candidate_flags:
        w = _weight_for_flag(flag, weights)
        if flag.valence == Valence.POSITIVE:
            total += w
        elif flag.valence == Valence.NEGATIVE:
            total -= w
    return total


def _compute_weighted_sums(
    candidate_flags: list[Flag],
    weights: dict[str, float],
) -> tuple[float, float]:
    """Return (positive_sum, negative_sum) for a candidate's flags."""
    pos = 0.0
    neg = 0.0
    for flag in candidate_flags:
        w = _weight_for_flag(flag, weights)
        if flag.valence == Valence.POSITIVE:
            pos += w
        elif flag.valence == Valence.NEGATIVE:
            neg += w
    return pos, neg


# ---------------------------------------------------------------------------
# Signal label computation
# ---------------------------------------------------------------------------


def _signal_label_from_sums(pos: float, neg: float, total_flags: int) -> SignalStrength:
    """Derive a SignalStrength label from weighted positive and negative sums.

    Thresholds:
        total_flags == 0              → INSUFFICIENT_DATA
        pos > 0 and neg == 0          → STRONG_POSITIVE
        pos > neg * 2                 → POSITIVE
        neg > pos * 2                 → NEGATIVE
        neg > 0 and pos == 0          → STRONG_NEGATIVE
        otherwise                     → MIXED
    """
    if total_flags == 0:
        return SignalStrength.INSUFFICIENT_DATA
    if pos == 0 and neg == 0:
        return SignalStrength.INSUFFICIENT_DATA
    if pos > 0 and neg == 0:
        return SignalStrength.STRONG_POSITIVE
    if neg > 0 and pos == 0:
        return SignalStrength.STRONG_NEGATIVE
    if pos > neg * 2:
        return SignalStrength.POSITIVE
    if neg > pos * 2:
        return SignalStrength.NEGATIVE
    return SignalStrength.MIXED


def _compute_signal_label(candidate_flags: list[Flag], weights: dict[str, float]) -> SignalStrength:
    """Compute signal-strength label for one candidate."""
    # Exclude ROUTING flags from signal computation (weight is 0.0 anyway,
    # but we also exclude them from the total_flags count for clarity).
    eval_flags = [f for f in candidate_flags if f.category != FlagCategory.ROUTING]
    pos, neg = _compute_weighted_sums(eval_flags, weights)
    return _signal_label_from_sums(pos, neg, len(eval_flags))


# ---------------------------------------------------------------------------
# Risk band computation
# ---------------------------------------------------------------------------


def _is_risk_flag(flag: Flag) -> bool:
    """Return True if this flag counts toward the risk band.

    EXPERIENCE_GAP flags only count if their active_priority metadata is 'high'.
    Medium/low priority gaps are background noise, not risk signals.
    """
    if flag.category in _RISK_CATEGORIES:
        return True
    if flag.category == FlagCategory.EXPERIENCE_GAP and flag.name in _HIGH_PRIORITY_EXPERIENCE_GAP_NAMES:
        return flag.metadata.get("active_priority") == "high"
    return False


def _count_risk_flags(candidate_flags: list[Flag]) -> int:
    """Count risk-contributing flags for a candidate."""
    return sum(1 for f in candidate_flags if _is_risk_flag(f))


def _risk_band_from_count(count: int) -> RiskBand:
    """Map risk flag count to a risk band.

    Thresholds:
        0       → LOW
        1-2     → MODERATE
        3-4     → ELEVATED
        5+      → HIGH
    """
    if count == 0:
        return RiskBand.LOW
    if count <= 2:
        return RiskBand.MODERATE
    if count <= 4:
        return RiskBand.ELEVATED
    return RiskBand.HIGH


def _has_personality_flags(candidate_flags: list[Flag]) -> bool:
    """Return True if the candidate has any personality (scored_flag) flags."""
    return any(f.evidence_type == EvidenceType.SCORED_FLAG for f in candidate_flags)


def _compute_risk_band(
    candidate: str,
    candidate_flags: list[Flag],
    assessment_mode: str,
    partial_mode_notes: list[str],
) -> RiskBand:
    """Compute risk band for one candidate, honouring partial-mode rules.

    Partial-mode candidates with no personality flags get INSUFFICIENT_DATA
    and a note is appended to partial_mode_notes.
    """
    if assessment_mode == "partial" and not _has_personality_flags(candidate_flags):
        partial_mode_notes.append(
            f"Candidate '{candidate}': Risk assessment limited to experience-based signals. "
            "Personality-based derailment risk not assessed."
        )
        return RiskBand.INSUFFICIENT_DATA

    count = _count_risk_flags(candidate_flags)
    return _risk_band_from_count(count)


# ---------------------------------------------------------------------------
# Tension map computation
# ---------------------------------------------------------------------------


def _get_cv_flag_domains(flag: Flag) -> list[str]:
    """Return domain(s) for a CV-derived flag."""
    domain = _CV_FLAG_DOMAIN.get(flag.category)
    return [domain] if domain else []


def _get_personality_flag_domains(flag: Flag) -> list[str]:
    """Return domain(s) for a personality flag."""
    domain = _PERSONALITY_FLAG_DOMAIN.get(flag.category)
    return [domain] if domain else []


def _build_cross_stream_tensions(candidate_flags: list[Flag], candidate_name: str) -> list[TensionPair]:
    """Find cross-stream tension pairs for one candidate.

    Cross-stream: positive CV flag + negative personality flag on same domain,
    or negative CV flag + positive personality flag on same domain.
    """
    cv_flags = [f for f in candidate_flags if f.evidence_type != EvidenceType.SCORED_FLAG]
    personality_flags = [f for f in candidate_flags if f.evidence_type == EvidenceType.SCORED_FLAG]

    tensions: list[TensionPair] = []

    for cv_flag in cv_flags:
        for cv_domain in _get_cv_flag_domains(cv_flag):
            for pf in personality_flags:
                for pf_domain in _get_personality_flag_domains(pf):
                    if cv_domain != pf_domain:
                        continue
                    # Positive CV + negative personality
                    if cv_flag.valence == Valence.POSITIVE and pf.valence == Valence.NEGATIVE:
                        tensions.append(
                            TensionPair(
                                candidate_name=candidate_name,
                                positive_flag=cv_flag.name,
                                negative_flag=pf.name,
                                domain=cv_domain,
                                tension_type="cross_stream",
                                description=(
                                    f"Strong CV evidence in '{cv_domain}' ({cv_flag.name}) "
                                    f"alongside personality risk ({pf.name}). "
                                    "Track record and personality profile diverge on this domain."
                                ),
                            )
                        )
                    # Negative CV + positive personality
                    elif cv_flag.valence == Valence.NEGATIVE and pf.valence == Valence.POSITIVE:
                        tensions.append(
                            TensionPair(
                                candidate_name=candidate_name,
                                positive_flag=pf.name,
                                negative_flag=cv_flag.name,
                                domain=cv_domain,
                                tension_type="cross_stream",
                                description=(
                                    f"CV gap in '{cv_domain}' ({cv_flag.name}) "
                                    f"alongside positive personality signal ({pf.name}). "
                                    "Personality capability not yet demonstrated in track record."
                                ),
                            )
                        )

    return tensions


def _build_intra_stream_tensions(candidate_flags: list[Flag], candidate_name: str) -> list[TensionPair]:
    """Find intra-stream tension pairs for one candidate.

    Intra-stream: positive flag + negative flag in the same category.
    """
    by_category: dict[FlagCategory, list[Flag]] = defaultdict(list)
    for flag in candidate_flags:
        by_category[flag.category].append(flag)

    tensions: list[TensionPair] = []
    for category, flags in by_category.items():
        positive_flags = [f for f in flags if f.valence == Valence.POSITIVE]
        negative_flags = [f for f in flags if f.valence == Valence.NEGATIVE]
        domain = _PERSONALITY_FLAG_DOMAIN.get(category) or _CV_FLAG_DOMAIN.get(category) or category.value
        for pos_flag in positive_flags:
            for neg_flag in negative_flags:
                tensions.append(
                    TensionPair(
                        candidate_name=candidate_name,
                        positive_flag=pos_flag.name,
                        negative_flag=neg_flag.name,
                        domain=domain,
                        tension_type="intra_stream",
                        description=(
                            f"Conflicting signals within '{category.value}': "
                            f"positive ({pos_flag.name}) alongside negative ({neg_flag.name}). "
                            "Mixed signals on this domain require closer evaluation."
                        ),
                    )
                )

    return tensions


def _build_tension_map(flags: list[Flag], candidate_names: list[str]) -> list[TensionPair]:
    """Build the full tension map across all candidates."""
    per_candidate: dict[str, list[Flag]] = defaultdict(list)
    for flag in flags:
        per_candidate[flag.candidate_name].append(flag)

    all_tensions: list[TensionPair] = []
    for candidate in candidate_names:
        candidate_flags = per_candidate.get(candidate, [])
        all_tensions.extend(_build_cross_stream_tensions(candidate_flags, candidate))
        all_tensions.extend(_build_intra_stream_tensions(candidate_flags, candidate))

    return all_tensions


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def compute_layer1(
    flags: list[Flag],
    scenario: ScenarioConfig,
    candidate_names: list[str],
    assessment_modes: dict[str, str],
) -> Layer1Output:
    """Compute scenario weights, signal labels, risk bands, and tension map.

    CRITICAL: The returned signal_labels and risk_bands must NOT be passed
    to agent inputs (F02). They are reserved for synthesis only.

    Args:
        flags: Validated flag set from Layer 0 (E1).
        scenario: Active ScenarioConfig carrying category weight overrides.
        candidate_names: Ordered list of candidate names for deterministic output.
        assessment_modes: Candidate name → "full" or "partial".

    Returns:
        Layer1Output containing weighted scores, signal labels, risk bands,
        tension map, and partial mode notes.
    """
    weights = _resolve_weights(scenario)

    # Group flags by candidate for per-candidate computations.
    per_candidate: dict[str, list[Flag]] = defaultdict(list)
    for flag in flags:
        per_candidate[flag.candidate_name].append(flag)

    weighted_scores: dict[str, float] = {}
    signal_labels: dict[str, SignalStrength] = {}
    risk_bands: dict[str, RiskBand] = {}
    partial_mode_notes: list[str] = []

    for candidate in candidate_names:
        candidate_flags = per_candidate.get(candidate, [])
        mode = assessment_modes.get(candidate, "full")

        weighted_scores[candidate] = _compute_weighted_score(candidate_flags, weights)
        signal_labels[candidate] = _compute_signal_label(candidate_flags, weights)
        risk_bands[candidate] = _compute_risk_band(candidate, candidate_flags, mode, partial_mode_notes)

    tension_map = _build_tension_map(flags, candidate_names)

    logger.debug(
        "Layer 1 complete: %d candidates, %d tensions, %d partial notes",
        len(candidate_names),
        len(tension_map),
        len(partial_mode_notes),
    )

    return Layer1Output(
        weighted_scores_per_candidate=weighted_scores,
        signal_labels=signal_labels,
        risk_bands=risk_bands,
        tension_map=tension_map,
        partial_mode_notes=partial_mode_notes,
    )
