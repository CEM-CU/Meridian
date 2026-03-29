"""Test fixtures package -- synthetic data for all pipeline stages.

Re-exports all fixture data so tests can import from fixtures directly:

    from fixtures import BMW_CTO_JD_TEXT, ALL_CANDIDATES, BIG_FIVE_PRESETS

Note: the ``tests/conftest.py`` adds ``tests/`` to ``sys.path`` so that
``fixtures`` is importable as a top-level package without needing a
``tests/__init__.py`` (which would conflict with stage-level test packages).
"""

from fixtures.big_five_presets import BIG_FIVE_PRESETS
from fixtures.synthetic_candidates import (
    ALL_CANDIDATES,
    CANDIDATE_KENJI,
    CANDIDATE_MARCUS,
    CANDIDATE_SARAH,
    KENJI_TANAKA_CV_TEXT,
    MARCUS_CHEN_BIG_FIVE,
    MARCUS_CHEN_CV_TEXT,
    SARAH_OKAFOR_BIG_FIVE,
    SARAH_OKAFOR_CV_TEXT,
)
from fixtures.synthetic_jd import BMW_CTO_JD_TEXT

__all__ = [
    "ALL_CANDIDATES",
    "BIG_FIVE_PRESETS",
    "BMW_CTO_JD_TEXT",
    "CANDIDATE_KENJI",
    "CANDIDATE_MARCUS",
    "CANDIDATE_SARAH",
    "KENJI_TANAKA_CV_TEXT",
    "MARCUS_CHEN_BIG_FIVE",
    "MARCUS_CHEN_CV_TEXT",
    "SARAH_OKAFOR_BIG_FIVE",
    "SARAH_OKAFOR_CV_TEXT",
]
