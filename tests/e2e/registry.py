"""Scenario registry and dynamic loader."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from meridian.models import CandidateData, ScenarioConfig

# Ensure fixtures are importable
_FIXTURES_DIR = str(Path(__file__).resolve().parent.parent / "fixtures")
if _FIXTURES_DIR not in sys.path:
    sys.path.insert(0, _FIXTURES_DIR)

# (display_name, module_name)
SCENARIOS: list[tuple[str, str]] = [
    ("VP Engineering", "vp_engineering"),
    ("Head of People", "head_of_people"),
    ("VP Operations", "vp_operations"),
    ("Head of Finance", "head_of_finance"),
    ("Director of Product", "director_of_product"),
    ("VP Sales", "vp_sales"),
    ("Director of Data", "director_of_data"),
    ("Head of Marketing", "head_of_marketing"),
    ("Director of Engineering", "director_of_engineering"),
]


def load_scenario(module_name: str) -> tuple[str, list[CandidateData], ScenarioConfig]:
    """Dynamically import a scenario and return (jd_text, candidates, config)."""
    mod = __import__(f"scenarios.{module_name}", fromlist=[module_name])
    return mod.JD_TEXT, mod.ALL_CANDIDATES, mod.SCENARIO_CONFIG
