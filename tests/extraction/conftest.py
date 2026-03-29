"""Local pytest conftest for extraction tests.

Re-exports fixtures from the root ``tests/conftest.py`` so that extraction
integration tests can reference ``synthetic_jd_text``, ``synthetic_candidates``,
``sample_requirements``, ``sample_rubric_assessments``, and
``sample_scenario_config`` when pytest is invoked against this directory
alone (e.g. ``uv run pytest tests/extraction/`` ).

The root conftest only loads when pytest discovers the ``tests/`` directory in
the project root as part of a full-suite run.  Importing and re-exposing the
same fixture constants here ensures isolated runs also work.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Ensure root tests/ directory is on sys.path so fixture sub-modules
# (fixtures.synthetic_jd, fixtures.synthetic_candidates) are importable.
# ---------------------------------------------------------------------------

_ROOT_TESTS_DIR = Path(__file__).resolve().parents[1]
_ROOT_TESTS_DIR_STR = str(_ROOT_TESTS_DIR)
if _ROOT_TESTS_DIR_STR not in sys.path:
    sys.path.insert(0, _ROOT_TESTS_DIR_STR)

# Also ensure extraction tests directory itself is on sys.path so _helpers is importable
_EXTRACTION_DIR = str(Path(__file__).resolve().parent)
if _EXTRACTION_DIR not in sys.path:
    sys.path.insert(0, _EXTRACTION_DIR)

# ---------------------------------------------------------------------------
# Load the root conftest module via importlib so we can access its private
# module-level constants without relying on a package import path.
# ---------------------------------------------------------------------------

_ROOT_CONFTEST_PATH = _ROOT_TESTS_DIR / "conftest.py"
_spec = importlib.util.spec_from_file_location("_root_conftest", _ROOT_CONFTEST_PATH)
assert _spec is not None and _spec.loader is not None
_root_conftest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_root_conftest)  # type: ignore[union-attr]

_ROOT_REQUIREMENTS = _root_conftest._REQUIREMENTS  # type: ignore[attr-defined]
_ROOT_RUBRIC_ASSESSMENTS = _root_conftest._RUBRIC_ASSESSMENTS  # type: ignore[attr-defined]
_ROOT_SCENARIO_CONFIG = _root_conftest._SCENARIO_CONFIG  # type: ignore[attr-defined]

from fixtures.synthetic_candidates import ALL_CANDIDATES  # type: ignore[import]  # noqa: E402
from fixtures.synthetic_jd import BMW_CTO_JD_TEXT  # type: ignore[import]  # noqa: E402

from meridian.models import CandidateData, Requirement, RubricAssessment, ScenarioConfig  # noqa: E402, TC001

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def synthetic_jd_text() -> str:
    """BMW CTO JD raw text."""
    return BMW_CTO_JD_TEXT


@pytest.fixture()
def synthetic_candidates() -> list[CandidateData]:
    """All 3 synthetic candidates (deep copies)."""
    return [c.model_copy(deep=True) for c in ALL_CANDIDATES]


@pytest.fixture()
def sample_requirements() -> list[Requirement]:
    """12 pre-built requirements matching the BMW CTO JD."""
    return [r.model_copy(deep=True) for r in _ROOT_REQUIREMENTS]


@pytest.fixture()
def sample_rubric_assessments() -> list[RubricAssessment]:
    """Pre-built rubric assessments for 3 candidates x 10 CV-assessable reqs."""
    return [a.model_copy(deep=True) for a in _ROOT_RUBRIC_ASSESSMENTS]


@pytest.fixture()
def sample_scenario_config() -> ScenarioConfig:
    """ScenarioConfig for digital_transformation scenario."""
    return _ROOT_SCENARIO_CONFIG.model_copy(deep=True)
