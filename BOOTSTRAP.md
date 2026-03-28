# BOOTSTRAP — Paste this as your first Claude Code prompt

You are initializing a monorepo for Meridian, a C-Suite Decision Intelligence Tool (BMW Hackathon). This is a multi-agent evaluation pipeline with stages C→D→E. Backend only, pure Python, no web framework. 16-hour build window.

Execute every step below in order. Do not skip steps. Do not ask questions — execute.

---

## Step 1: Verify tooling

```bash
uv --version    # must be installed
just --version  # must be installed
git --version   # must be installed
```

If any is missing, tell me and stop. Do not attempt to install them.

---

## Step 2: Initialize git repo

```bash
git init
git checkout -b main
```

---

## Step 3: Create the full directory skeleton

Create all directories AND empty `__init__.py` files where marked:

```
.claude/
.orchestrator/
shared/
  src/shared/
    __init__.py
    models/
      __init__.py
    utils/
      __init__.py
  tests/
    __init__.py
stages/
  stage_c/
    .agent/
    src/stage_c/
      __init__.py
      prompts/
        __init__.py
    tests/
      __init__.py
  stage_d/
    .agent/
    src/stage_d/
      __init__.py
      config/
        __init__.py
    tests/
      __init__.py
  stage_e/
    .agent/
    src/stage_e/
      __init__.py
      layer2_agents/
        __init__.py
        prompts/
          __init__.py
      layer3_audit/
        __init__.py
      synthesis/
        __init__.py
    tests/
      __init__.py
tests/
  fixtures/
  e2e/
    __init__.py
```

---

## Step 4: Place the pre-written files

I have pre-written files that you need to place. Read them from `BOOTSTRAP_FILES/` in the current directory and copy them to their correct locations:

```
BOOTSTRAP_FILES/.claude/CLAUDE.md                           → .claude/CLAUDE.md
BOOTSTRAP_FILES/.orchestrator/status.md                     → .orchestrator/status.md
BOOTSTRAP_FILES/.orchestrator/blockers.md                   → .orchestrator/blockers.md
BOOTSTRAP_FILES/.orchestrator/decisions.md                  → .orchestrator/decisions.md
BOOTSTRAP_FILES/.orchestrator/errors.md                     → .orchestrator/errors.md
BOOTSTRAP_FILES/.orchestrator/interfaces.md                 → .orchestrator/interfaces.md
BOOTSTRAP_FILES/stages/stage_c/.agent/tasks.md              → stages/stage_c/.agent/tasks.md
BOOTSTRAP_FILES/stages/stage_c/.agent/edge_cases.md         → stages/stage_c/.agent/edge_cases.md
BOOTSTRAP_FILES/stages/stage_c/.agent/implementation_notes.md → stages/stage_c/.agent/implementation_notes.md
BOOTSTRAP_FILES/stages/stage_c/.agent/test_plan.md          → stages/stage_c/.agent/test_plan.md
BOOTSTRAP_FILES/stages/stage_d/.agent/tasks.md              → stages/stage_d/.agent/tasks.md
BOOTSTRAP_FILES/stages/stage_d/.agent/edge_cases.md         → stages/stage_d/.agent/edge_cases.md
BOOTSTRAP_FILES/stages/stage_d/.agent/implementation_notes.md → stages/stage_d/.agent/implementation_notes.md
BOOTSTRAP_FILES/stages/stage_d/.agent/test_plan.md          → stages/stage_d/.agent/test_plan.md
BOOTSTRAP_FILES/stages/stage_e/.agent/tasks.md              → stages/stage_e/.agent/tasks.md
BOOTSTRAP_FILES/stages/stage_e/.agent/edge_cases.md         → stages/stage_e/.agent/edge_cases.md
BOOTSTRAP_FILES/stages/stage_e/.agent/implementation_notes.md → stages/stage_e/.agent/implementation_notes.md
BOOTSTRAP_FILES/stages/stage_e/.agent/test_plan.md          → stages/stage_e/.agent/test_plan.md
BOOTSTRAP_FILES/justfile                                     → justfile
BOOTSTRAP_FILES/pyproject.toml                               → pyproject.toml
```

---

## Step 5: Create per-package pyproject.toml files

### shared/pyproject.toml

```toml
[project]
name = "shared"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.10",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/shared"]
```

### stages/stage_c/pyproject.toml

```toml
[project]
name = "stage-c"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "shared",
    "httpx>=0.28",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/stage_c"]
```

### stages/stage_d/pyproject.toml

```toml
[project]
name = "stage-d"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "shared",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/stage_d"]
```

### stages/stage_e/pyproject.toml

```toml
[project]
name = "stage-e"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "shared",
    "httpx>=0.28",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/stage_e"]
```

---

## Step 6: Create shared Pydantic models

These are the inter-stage contracts. Every stage imports from these. Create the following files:

### shared/src/shared/models/__init__.py

Export all models from this package:

```python
from shared.models.requirements import Requirement, Priority, ScenarioPriority
from shared.models.rubric import RubricAssessment, RubricLevel, Confidence
from shared.models.flags import Flag, FlagCategory, Valence, EvidenceType
from shared.models.candidates import CandidateData, BigFiveScores, TeamMember
from shared.models.scenarios import ScenarioConfig, ScenarioName
from shared.models.pipeline import StageCOutput, StageDOutput, FlagProvenance, AssessmentMode

__all__ = [
    "Requirement", "Priority", "ScenarioPriority",
    "RubricAssessment", "RubricLevel", "Confidence",
    "Flag", "FlagCategory", "Valence", "EvidenceType",
    "CandidateData", "BigFiveScores", "TeamMember",
    "ScenarioConfig", "ScenarioName",
    "StageCOutput", "StageDOutput", "FlagProvenance", "AssessmentMode",
]
```

### shared/src/shared/models/requirements.py

```python
"""JD requirement extraction models. Produced by Stage C1, consumed by C2/C3/C4/D/E."""

from enum import StrEnum
from pydantic import BaseModel, Field


class Priority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ScenarioPriority(BaseModel):
    """Per-requirement priority under each scenario. Assigned by LLM during C1 extraction."""

    digital_transformation: Priority
    post_acquisition: Priority
    turnaround: Priority
    stabilization: Priority
    growth: Priority

    def for_scenario(self, scenario_name: str) -> Priority:
        return getattr(self, scenario_name)


class Requirement(BaseModel):
    """Single assessable requirement extracted from a JD."""

    requirement_id: str = Field(description="Sequential ID: REQ-01 through REQ-N")
    text: str = Field(max_length=200, description="Normalized requirement statement")
    source_quote: str = Field(max_length=300, description="Verbatim or near-verbatim from JD")
    assessable_from_cv: bool = Field(description="False for behavioral requirements, true otherwise. LLM assigns during extraction.")
    scenario_priority: ScenarioPriority = Field(description="LLM assigns priority per scenario during C1 extraction")
```

### shared/src/shared/models/rubric.py

```python
"""CV rubric assessment models. Produced by Stage C3, consumed by C4/D/E."""

from enum import StrEnum
from pydantic import BaseModel, Field


class RubricLevel(StrEnum):
    EXCEEDS = "exceeds"
    MEETS = "meets"
    PARTIAL = "partial"
    GAP = "gap"
    NOT_ASSESSABLE = "not_assessable"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RubricAssessment(BaseModel):
    """Single rubric evaluation: one requirement × one candidate."""

    requirement_id: str
    candidate_name: str
    rubric_level: RubricLevel
    confidence: Confidence
    cv_citation: str | None = Field(default=None, description="Specific CV passage. Required for EXCEEDS/MEETS/PARTIAL")
    cv_location: str | None = Field(default=None, description="Role name, section, or paragraph reference")
    notes: str | None = Field(default=None, description="Assessor notes, recency concerns, conflicts")
    investigation_question: str | None = Field(default=None, description="Specific question for GAP/PARTIAL/low-confidence")
```

### shared/src/shared/models/flags.py

```python
"""Flag models. Produced by Stage D, consumed by Stage E."""

from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field


class FlagCategory(StrEnum):
    EXECUTION = "EXECUTION"
    STRATEGIC = "STRATEGIC"
    COLLISION = "COLLISION"
    COMPLEMENT = "COMPLEMENT"
    FRICTION = "FRICTION"
    CULTURAL = "CULTURAL"
    DERAILMENT = "DERAILMENT"
    DARK_SIDE = "DARK_SIDE"
    INTEGRATION = "INTEGRATION"
    TENURE = "TENURE"
    GROUPTHINK = "GROUPTHINK"
    EXPERIENCE_STRENGTH = "EXPERIENCE_STRENGTH"
    EXPERIENCE_GAP = "EXPERIENCE_GAP"
    EVIDENCE_QUALITY = "EVIDENCE_QUALITY"
    ROUTING = "ROUTING"


class Valence(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class EvidenceType(StrEnum):
    SCORED_FLAG = "scored_flag"
    CV_RUBRIC = "cv_rubric"
    REQUIREMENT_GAP = "requirement_gap"
    CV_PATTERN = "cv_pattern"
    ROUTING = "routing"


class Flag(BaseModel):
    """Single flag in the merged flag set. Both personality and CV-derived flags use this model."""

    name: str
    candidate_name: str
    category: FlagCategory
    valence: Valence
    evidence_type: EvidenceType
    topic_keywords: list[str] = Field(default_factory=list)

    # Personality flag fields (None for CV-derived flags)
    big_five_source: str | None = Field(default=None, description="O, C, E, A, or N")
    big_five_score: float | None = Field(default=None)
    threshold_used: float | None = Field(default=None)

    # CV-derived flag fields (None for personality flags)
    requirement_id: str | None = Field(default=None)
    rubric_level: str | None = Field(default=None)
    cv_citation: str | None = Field(default=None)
    confidence: str | None = Field(default=None)
    notes: str | None = Field(default=None)
    investigation_question: str | None = Field(default=None)

    metadata: dict[str, Any] = Field(default_factory=dict)
```

### shared/src/shared/models/candidates.py

```python
"""Candidate data models. Input to pipeline, passed through to Stage E."""

from pydantic import BaseModel, Field


class BigFiveScores(BaseModel):
    """OCEAN scores, each 0.0 to 1.0."""

    O: float = Field(ge=0.0, le=1.0, description="Openness")
    C: float = Field(ge=0.0, le=1.0, description="Conscientiousness")
    E: float = Field(ge=0.0, le=1.0, description="Extraversion")
    A: float = Field(ge=0.0, le=1.0, description="Agreeableness")
    N: float = Field(ge=0.0, le=1.0, description="Neuroticism")


class TeamMember(BaseModel):
    """Existing C-suite team member for complementarity/collision analysis."""

    name: str
    role: str
    big_five: BigFiveScores


class CandidateData(BaseModel):
    """Full candidate data passed through the pipeline."""

    name: str
    cv_text: str = Field(description="Raw CV text — ground truth for F04 validation")
    big_five: BigFiveScores | None = Field(default=None)
    personality_source: str | None = Field(default=None, description="'manual', 'Preset — {name}', 'Modified preset — {name}'")
    team_context: list[TeamMember] = Field(default_factory=list)
```

### shared/src/shared/models/scenarios.py

```python
"""Scenario configuration."""

from enum import StrEnum
from pydantic import BaseModel, Field


class ScenarioName(StrEnum):
    DIGITAL_TRANSFORMATION = "digital_transformation"
    POST_ACQUISITION = "post_acquisition"
    TURNAROUND = "turnaround"
    STABILIZATION = "stabilization"
    GROWTH = "growth"


class ScenarioConfig(BaseModel):
    """Active scenario. Priority per requirement is stored ON the requirement (ScenarioPriority),
    not in a global lookup table. This model carries the active scenario name and Layer 1 weight vectors."""

    name: ScenarioName
    category_weights: dict[str, float] = Field(default_factory=dict, description="FlagCategory → weight for Layer 1")
```

### shared/src/shared/models/pipeline.py

```python
"""Pipeline inter-stage data containers."""

from enum import StrEnum
from pydantic import BaseModel, Field
from shared.models.requirements import Requirement
from shared.models.rubric import RubricAssessment
from shared.models.flags import Flag
from shared.models.candidates import CandidateData
from shared.models.scenarios import ScenarioConfig


class AssessmentMode(StrEnum):
    FULL = "full"
    PARTIAL = "partial"


class FlagProvenance(BaseModel):
    """Per-candidate provenance metadata for the flag set."""

    assessment_mode: AssessmentMode
    personality_flag_count: int = 0
    cv_flag_count: int = 0
    total_flags: int = 0
    big_five_available: bool = False
    personality_source: str | None = None
    requirements_assessed: int = 0
    high_priority_gap_count: int = 0
    dimension_coverage_warnings: list[str] = Field(default_factory=list)
    cross_stream_coherence_notes: list[str] = Field(default_factory=list)


class StageCOutput(BaseModel):
    """Stage C → Stage D contract."""

    requirements: list[Requirement]
    rubric_assessments: list[RubricAssessment]
    candidate_data: list[CandidateData]
    scenario: ScenarioConfig


class StageDOutput(BaseModel):
    """Stage D → Stage E contract."""

    flags: list[Flag]
    provenance_per_candidate: dict[str, FlagProvenance]
    confirmed_requirements: list[Requirement]
    candidate_data: list[CandidateData]
    rubric_matrix: list[RubricAssessment]
    scenario: ScenarioConfig
```

---

## Step 7: Create shared utilities stub

### shared/src/shared/utils/__init__.py

```python
from shared.utils.llm_client import LLMClient

__all__ = ["LLMClient"]
```

### shared/src/shared/utils/llm_client.py

```python
"""Shared LLM client. All LLM calls in the pipeline go through this.

Uses httpx.AsyncClient. Handles: API key from env, model selection,
retry with exponential backoff (max 2), timeout (30s), response parsing,
structured logging of token usage.
"""

# TODO: Implement after shared models are verified.
# Placeholder so imports don't break.


class LLMClient:
    """Async LLM client for structured JSON completions."""

    pass
```

---

## Step 8: Create .gitignore

```
__pycache__/
*.pyc
.venv/
*.egg-info/
dist/
.ruff_cache/
.pyright/
.pytest_cache/
uv.lock
```

---

## Step 9: Install dependencies

```bash
uv sync
```

Verify the workspace resolves correctly. If there are resolution errors, fix the pyproject.toml files.

---

## Step 10: Verify shared models import correctly

```bash
uv run python -c "from shared.models import Flag, Requirement, RubricAssessment, CandidateData, ScenarioConfig, StageCOutput, StageDOutput; print('All shared models import OK')"
```

If this fails, fix import paths before proceeding.

---

## Step 11: Create git branch structure

```bash
git add -A
git commit -m "bootstrap: repo skeleton, shared models, orchestrator context"
git branch stage-c
git branch stage-d
git branch stage-e
```

---

## Step 12: Run lint to verify clean state

```bash
just lint
```

Fix any issues. The repo must be lint-clean before any feature work begins.

---

## Step 13: Report status

After completing all steps, read `.orchestrator/status.md` and confirm:
1. All shared model components show DONE
2. All stage tasks show NOT STARTED
3. No blockers prevent starting Layer 1 work (D personality flags ∥ C4 bridge)

Print the output of `just status` to confirm.
