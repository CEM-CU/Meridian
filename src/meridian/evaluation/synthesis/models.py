"""Stage-specific Pydantic models for the E7 synthesis output.

These models represent the three progressive-disclosure layers of the
synthesis document the CHRO reads. They are stage-specific and must NOT
be moved to shared/models/ — only cross-boundary contracts belong there.
"""

from pydantic import BaseModel, ConfigDict


class TradeOffCell(BaseModel):
    """Single cell in the trade-off matrix.

    Each cell sits at the intersection of one requirement row and one
    candidate column. The active_priority reflects the current scenario's
    priority for that requirement — rows are sorted by this value.
    """

    model_config = ConfigDict(extra="forbid")

    requirement_id: str
    requirement_text: str
    active_priority: str  # high / medium / low
    candidate_name: str
    rubric_level: str  # exceeds / meets / partial / gap / not_assessable
    confidence: str  # high / medium / low
    cv_citation: str | None = None
    investigation_question: str | None = None


class ContestedSignal(BaseModel):
    """A signal where agents disagree or cross-stream tension exists (F12).

    Two contest types:
    - cross_agent: same flag cited by multiple agents with different valence.
    - cross_stream: role-fit cites strong CV evidence on a domain while risk
      cites a personality flag on the same domain.
    """

    model_config = ConfigDict(extra="forbid")

    candidate_name: str
    signal_type: str  # "cross_agent" or "cross_stream"
    description: str
    agents_involved: list[str]


class CandidateSummary(BaseModel):
    """Per-candidate Layer 2 summary.

    Produced from audited agent verdicts. The CHRO expands this by clicking
    a candidate column header in the trade-off matrix.
    """

    model_config = ConfigDict(extra="forbid")

    candidate_name: str
    assessment_mode: str  # "full" or "partial"
    agent_highlights: dict[str, str]  # agent_role → summary text
    contested_signals: list[ContestedSignal]
    investigation_questions: list[str]
    unaddressed_flags: list[str]


class ProvenanceHeader(BaseModel):
    """Data provenance and quality metadata (F08).

    Summarises both data sources (JD + CV + Big Five) and the quality checks
    that passed or failed during Layer 0 validation.
    """

    model_config = ConfigDict(extra="forbid")

    requirement_count: int
    cv_assessable_count: int
    behavioral_count: int
    candidate_count: int
    assessment_modes: dict[str, str]  # candidate → "full" or "partial"
    personality_sources: dict[str, str | None]  # candidate → source string or None
    flag_counts: dict[str, int]  # candidate → total flags
    quality_checks_passed: bool
    warnings: list[str]


class SynthesisOutput(BaseModel):
    """Complete Stage E synthesis output.

    Three progressive-disclosure layers assembled in assembler.py:
    - Layer 1: trade_off_matrix (primary view)
    - Layer 2: candidate_summaries (per-candidate agent debate)
    - Layer 3: full evidence trail is represented inline via trade_off_matrix
      cells (cv_citation, investigation_question) and candidate_summaries.

    The trade_off_statement is the single LLM-generated summary (2-4 sentences).
    """

    model_config = ConfigDict(extra="forbid")

    provenance: ProvenanceHeader
    trade_off_matrix: list[TradeOffCell]
    candidate_summaries: list[CandidateSummary]
    trade_off_statement: str  # 2-4 sentences from LLM
    contested_signals: list[ContestedSignal]
    epistemic_disclaimer: str  # F10: always present
    partial_mode_disclaimer: str | None = None  # F09: only when partial mode candidates exist
