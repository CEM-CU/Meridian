"""SSE event type definitions for the evaluation pipeline.

Each event type corresponds to a pipeline checkpoint. Events carry
JSON-serializable data payloads. The frontend consumes these via EventSource.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

# ---------------------------------------------------------------------------
# Event type enum
# ---------------------------------------------------------------------------


class SSEEventType(StrEnum):
    """All event types emitted by the evaluation pipeline SSE stream."""

    # Input / job lifecycle
    JOB_CREATED = "job_created"

    # Stage C — JD extraction + CV rubric assessment
    C1_STARTED = "c1_started"
    C1_COMPLETE = "c1_complete"
    C2_COMPLETE = "c2_complete"
    C3_STARTED = "c3_started"
    C3_CANDIDATE_DONE = "c3_candidate_done"
    C4_COMPLETE = "c4_complete"

    # Stage D — deterministic flag derivation
    STAGE_D_COMPLETE = "stage_d_complete"

    # Stage E — multi-agent evaluation + synthesis
    SIGNALS_COMPUTED = "signals_computed"
    AGENTS_STARTED = "agents_started"
    AGENT_COMPLETE = "agent_complete"
    AGENT_TIMEOUT = "agent_timeout"
    AUDIT_COMPLETE = "audit_complete"
    SYNTHESIS_STARTED = "synthesis_started"
    SYNTHESIS_COMPLETE = "synthesis_complete"

    # Scenario switch
    SWITCH_STARTED = "switch_started"
    SWITCH_COMPLETE = "switch_complete"

    # Terminal
    COMPLETE = "complete"
    ERROR = "error"


# ---------------------------------------------------------------------------
# Per-event payload models
# ---------------------------------------------------------------------------


class JobCreatedPayload(BaseModel):
    """Emitted when the job is accepted and queued."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    scenario: str
    candidate_count: int
    created_at: str  # ISO 8601


class C1StartedPayload(BaseModel):
    """Emitted when JD extraction begins."""

    model_config = ConfigDict(extra="forbid")

    job_id: str


class C1CompletePayload(BaseModel):
    """Emitted when JD extraction finishes.

    ``requirements`` is a list of serialized Requirement dicts.
    ``cv_assessable`` counts requirements with assessable_from_cv=True.
    ``behavioral`` counts behavioral / non-cv-assessable requirements.
    ``warnings`` carries any extraction-level warnings from the LLM.
    """

    model_config = ConfigDict(extra="forbid")

    requirements: list[dict]  # serialized Requirement list
    cv_assessable: int
    behavioral: int
    warnings: list[str]


class C2CompletePayload(BaseModel):
    """Emitted when active priority resolution finishes.

    ``scenario`` is the resolved ScenarioName string.
    ``requirement_count`` is the number of requirements with assigned priorities.
    """

    model_config = ConfigDict(extra="forbid")

    scenario: str
    requirement_count: int


class C3StartedPayload(BaseModel):
    """Emitted when CV rubric assessment batch begins."""

    model_config = ConfigDict(extra="forbid")

    candidate_count: int
    requirement_count: int


class C3CandidateDonePayload(BaseModel):
    """Emitted after rubric assessment completes for a single candidate.

    ``candidate`` is the candidate name.
    ``cells`` is the list of serialized RubricAssessment dicts.
    ``stats`` maps rubric level names to counts:
        {exceeds, meets, partial, gap, not_assessable}.
    ``done`` is the number of candidates completed so far.
    ``total`` is the total candidate count for this job.
    """

    model_config = ConfigDict(extra="forbid")

    candidate: str
    cells: list[dict]  # serialized rubric assessment cells
    stats: dict[str, int]  # {exceeds: N, meets: N, partial: N, gap: N, not_assessable: N}
    done: int
    total: int


class C4CompletePayload(BaseModel):
    """Emitted when the rubric-to-flag bridge finishes.

    ``cv_flag_count`` is the number of CV-derived flags produced.
    ``drop_count`` is the number of requirements dropped (not_assessable).
    """

    model_config = ConfigDict(extra="forbid")

    cv_flag_count: int
    drop_count: int


class StageDCompletePayload(BaseModel):
    """Emitted when Stage D (deterministic flag derivation) finishes.

    ``flag_count`` is the total merged flag count.
    ``personality_flag_count`` is flags derived from Big Five scores.
    ``cv_flag_count`` is flags derived from rubric assessment.
    ``validation_warnings`` carries any flag-level validation warnings.
    ``assessment_modes`` maps candidate name to 'full' or 'partial'.
    ``per_candidate`` maps candidate name to provenance details dict with
        keys: mode, personality_flags, cv_flags, total, big_five_available.
    """

    model_config = ConfigDict(extra="forbid")

    flag_count: int
    personality_flag_count: int
    cv_flag_count: int
    validation_warnings: list[str]
    assessment_modes: dict[str, str]
    per_candidate: dict[str, dict]  # name → {mode, personality_flags, cv_flags, total, big_five_available}


class SignalsComputedPayload(BaseModel):
    """Emitted when Stage E Layer 1 signal computation finishes.

    ``signal_count`` is the number of weighted signals.
    ``tension_pairs`` is the count of detected flag-tension pairs.
    ``scenario`` is the active scenario name.
    ``signal_labels`` maps candidate name to signal strength label.
    ``risk_bands`` maps candidate name to risk band label.
    ``tensions`` is the serialized TensionPair list (dicts with candidate_name,
        positive_flag, negative_flag, domain, tension_type, description).
    ``partial_mode_notes`` carries any partial-mode computation notes.
    """

    model_config = ConfigDict(extra="forbid")

    signal_count: int
    tension_pairs: int
    scenario: str
    signal_labels: dict[str, str]  # candidate → signal strength
    risk_bands: dict[str, str]  # candidate → risk band
    tensions: list[dict]  # serialized TensionPair list
    partial_mode_notes: list[str]


class AgentsStartedPayload(BaseModel):
    """Emitted when Stage E Layer 2 parallel agent calls begin."""

    model_config = ConfigDict(extra="forbid")

    agent_names: list[str]


class AgentCompletePayload(BaseModel):
    """Emitted when a single Stage E evaluation agent finishes.

    ``agent_name`` identifies the agent (e.g. 'execution', 'strategic', 'cultural').
    ``finding_count`` is the number of findings returned.
    ``evidence_count`` is the number of evidence items across all findings.
    ``elapsed_seconds`` is the wall-clock time for this agent call.
    ``summary`` is the agent's overall assessment summary text.
    ``evidence_types`` maps evidence type strings to their counts.
    ``unaddressed_flags`` lists flag names the agent left unaddressed.
    """

    model_config = ConfigDict(extra="forbid")

    agent_name: str
    finding_count: int
    evidence_count: int
    elapsed_seconds: float
    summary: str
    evidence_types: dict[str, int]  # type → count
    unaddressed_flags: list[str]


class AgentTimeoutPayload(BaseModel):
    """Emitted when a Stage E agent call exceeds its deadline.

    ``agent_name`` identifies the timed-out agent.
    ``timeout_seconds`` is the deadline that was exceeded.
    """

    model_config = ConfigDict(extra="forbid")

    agent_name: str
    timeout_seconds: float


class AuditCompletePayload(BaseModel):
    """Emitted when Stage E Layer 3 audit finishes.

    ``checks_run`` is the total number of audit checks executed.
    ``checks_passed`` is the number that passed.
    ``checks_failed`` is the number that failed.
    ``audit_warnings`` lists any audit-level warnings.
    """

    model_config = ConfigDict(extra="forbid")

    checks_run: int
    checks_passed: int
    checks_failed: int
    audit_warnings: list[str]


class SynthesisStartedPayload(BaseModel):
    """Emitted when Stage E synthesis LLM call begins."""

    model_config = ConfigDict(extra="forbid")

    candidate_count: int


class SynthesisCompletePayload(BaseModel):
    """Emitted when Stage E synthesis finishes.

    ``candidates`` maps each candidate name to their top-level verdict.
    ``trade_off_count`` is the number of trade-off pairs identified.
    ``investigation_question_count`` is the total investigation question count.
    ``trade_off_matrix`` is the full serialized trade-off matrix (list of dicts).
    ``candidate_summaries`` is the full serialized per-candidate summaries.
    ``trade_off_statement`` is the LLM-generated 2-4 sentence summary.
    ``contested_signals`` is the serialized list of contested signal dicts.
    ``provenance`` is the serialized ProvenanceHeader dict.
    ``epistemic_disclaimer`` is the always-present epistemic disclaimer text.
    ``partial_mode_disclaimer`` is present only when partial-mode candidates exist.
    """

    model_config = ConfigDict(extra="forbid")

    candidates: dict[str, str]  # candidate_name → verdict label
    trade_off_count: int
    investigation_question_count: int
    trade_off_matrix: list[dict]
    candidate_summaries: list[dict]
    trade_off_statement: str
    contested_signals: list[dict]
    provenance: dict
    epistemic_disclaimer: str
    partial_mode_disclaimer: str | None = None


class SwitchStartedPayload(BaseModel):
    """Emitted when a scenario switch begins.

    ``from_scenario`` and ``to_scenario`` identify the transition.
    ``job_id`` is the originating evaluation job.
    """

    model_config = ConfigDict(extra="forbid")

    job_id: str
    from_scenario: str
    to_scenario: str


class SwitchCompletePayload(BaseModel):
    """Emitted when a scenario switch finishes.

    ``job_id`` is the originating evaluation job.
    ``new_scenario`` is the active scenario after the switch.
    ``reused_rubric_cells`` is the count of rubric cells reused (no re-assessment).
    """

    model_config = ConfigDict(extra="forbid")

    job_id: str
    new_scenario: str
    reused_rubric_cells: int


class CompletePayload(BaseModel):
    """Emitted as the final terminal event when the pipeline succeeds.

    ``job_id`` is the evaluation job.
    ``elapsed_seconds`` is the total wall-clock time for the job.
    ``result_summary`` is a brief human-readable description of results.
    """

    model_config = ConfigDict(extra="forbid")

    job_id: str
    elapsed_seconds: float
    result_summary: str


class ErrorPayload(BaseModel):
    """Emitted as the terminal event when the pipeline fails.

    ``job_id`` is the evaluation job (if known).
    ``code`` is a short machine-readable error code.
    ``message`` is the user-facing error message.
    ``stage`` identifies where in the pipeline the error occurred (optional).
    """

    model_config = ConfigDict(extra="forbid")

    job_id: str | None
    code: str
    message: str
    stage: str | None = None


# ---------------------------------------------------------------------------
# Generic SSE event wrapper
# ---------------------------------------------------------------------------


class SSEEvent(BaseModel):
    """A single SSE event ready for wire format.

    ``event`` identifies the event type for EventSource routing.
    ``data`` is the JSON-serializable payload dict.
    """

    model_config = ConfigDict(extra="forbid")

    event: SSEEventType
    data: dict  # JSON-serializable payload


# ---------------------------------------------------------------------------
# Convenience mapping: event type → payload model class
# ---------------------------------------------------------------------------

PAYLOAD_MODELS: dict[SSEEventType, type[BaseModel]] = {
    SSEEventType.JOB_CREATED: JobCreatedPayload,
    SSEEventType.C1_STARTED: C1StartedPayload,
    SSEEventType.C1_COMPLETE: C1CompletePayload,
    SSEEventType.C2_COMPLETE: C2CompletePayload,
    SSEEventType.C3_STARTED: C3StartedPayload,
    SSEEventType.C3_CANDIDATE_DONE: C3CandidateDonePayload,
    SSEEventType.C4_COMPLETE: C4CompletePayload,
    SSEEventType.STAGE_D_COMPLETE: StageDCompletePayload,
    SSEEventType.SIGNALS_COMPUTED: SignalsComputedPayload,
    SSEEventType.AGENTS_STARTED: AgentsStartedPayload,
    SSEEventType.AGENT_COMPLETE: AgentCompletePayload,
    SSEEventType.AGENT_TIMEOUT: AgentTimeoutPayload,
    SSEEventType.AUDIT_COMPLETE: AuditCompletePayload,
    SSEEventType.SYNTHESIS_STARTED: SynthesisStartedPayload,
    SSEEventType.SYNTHESIS_COMPLETE: SynthesisCompletePayload,
    SSEEventType.SWITCH_STARTED: SwitchStartedPayload,
    SSEEventType.SWITCH_COMPLETE: SwitchCompletePayload,
    SSEEventType.COMPLETE: CompletePayload,
    SSEEventType.ERROR: ErrorPayload,
}
