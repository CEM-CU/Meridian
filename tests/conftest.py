"""Root conftest — pytest fixtures exposing synthetic test data for all test modules.

Every fixture returns a fresh copy (via model_copy / list copy) so tests remain
isolated even if a fixture value is accidentally mutated.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the tests/ directory is on sys.path so ``fixtures`` is importable
# as a top-level package without requiring a ``tests/__init__.py`` (which
# would conflict with stage-level ``tests/`` packages).
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

import pytest  # noqa: E402
from fixtures.big_five_presets import BIG_FIVE_PRESETS  # noqa: E402
from fixtures.synthetic_candidates import (  # noqa: E402
    ALL_CANDIDATES,
    CANDIDATE_KENJI,
    CANDIDATE_MARCUS,
    CANDIDATE_SARAH,
)
from fixtures.synthetic_jd import BMW_CTO_JD_TEXT  # noqa: E402

from meridian.models import (  # noqa: E402
    BigFiveScores,
    CandidateData,
    Confidence,
    Priority,
    Requirement,
    RubricAssessment,
    RubricLevel,
    ScenarioConfig,
    ScenarioName,
    ScenarioPriority,
)

# ---------------------------------------------------------------------------
# Raw text / candidate fixtures
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
def candidate_marcus() -> CandidateData:
    """Marcus Chen -- strong tech/scope, gap on industry."""
    return CANDIDATE_MARCUS.model_copy(deep=True)


@pytest.fixture()
def candidate_sarah() -> CandidateData:
    """Sarah Okafor -- strong industry/experience, partial technical."""
    return CANDIDATE_SARAH.model_copy(deep=True)


@pytest.fixture()
def candidate_kenji() -> CandidateData:
    """Kenji Tanaka -- balanced, gap on scope, no Big Five."""
    return CANDIDATE_KENJI.model_copy(deep=True)


@pytest.fixture()
def big_five_presets() -> dict[str, BigFiveScores]:
    """5 archetype presets (deep copies)."""
    return {name: scores.model_copy(deep=True) for name, scores in BIG_FIVE_PRESETS.items()}


# ---------------------------------------------------------------------------
# Pre-built requirements (12 requirements matching the BMW CTO JD)
# ---------------------------------------------------------------------------

_REQUIREMENTS: list[Requirement] = [
    Requirement(
        requirement_id="REQ-01",
        text=("12+ years progressive technology leadership in automotive, mobility, or adjacent deep-tech"),
        source_quote=(
            "12+ years of progressive technology leadership "
            "experience in automotive, mobility, or adjacent "
            "deep-tech sectors"
        ),
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.HIGH,
            turnaround=Priority.HIGH,
            stabilization=Priority.MEDIUM,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-02",
        text="P&L accountability of USD 500M+ or equivalent",
        source_quote="managing a P&L of USD 500M+ (or equivalent)",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.HIGH,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-03",
        text=("Led engineering organisations of 200+ across multiple geographies"),
        source_quote=("leading engineering organisations of 200+ people across multiple geographies"),
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.HIGH,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.MEDIUM,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-04",
        text=("Deep technical fluency in EV powertrain architecture or SDV middleware"),
        source_quote=("Deep technical fluency in at least two of: EV powertrain architecture, SDV middleware"),
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.LOW,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-05",
        text=("Track record of successful post-acquisition technology integration"),
        source_quote=(
            "Track record of successful post-acquisition technology integration -- harmonising teams, tech stacks"
        ),
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.HIGH,
            turnaround=Priority.HIGH,
            stabilization=Priority.LOW,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-06",
        text=("Experience in premium automotive or tier-1 supplier environments"),
        source_quote=("Experience operating in premium automotive or tier-1 supplier environments"),
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-07",
        text=("Direct technology delivery accountability in EMEA and APAC markets"),
        source_quote=("Direct accountability for technology delivery in both EMEA and APAC markets"),
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.HIGH,
            turnaround=Priority.LOW,
            stabilization=Priority.MEDIUM,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-08",
        text=("MBA, MS, or PhD in engineering, computer science, or related technical discipline"),
        source_quote=("MBA, MS, or PhD in engineering, computer science, or a related technical discipline"),
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.LOW,
            turnaround=Priority.LOW,
            stabilization=Priority.LOW,
            growth=Priority.LOW,
        ),
    ),
    Requirement(
        requirement_id="REQ-09",
        text="Professional fluency in English and German",
        source_quote=("Professional fluency in English (business language) and German (working language)"),
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.MEDIUM,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-10",
        text=("Track record leading large-scale digital transformation programmes"),
        source_quote=(
            "Track record of leading large-scale digital transformation programmes spanning multiple business units"
        ),
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.LOW,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-11",
        text=("Ability to navigate complex stakeholder landscapes including board members and works councils"),
        source_quote=(
            "Proven ability to navigate complex stakeholder "
            "landscapes involving board members, works councils, "
            "regulators"
        ),
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.HIGH,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-12",
        text=("Comfort operating in consensus-driven corporate culture while driving software delivery urgency"),
        source_quote=(
            "Comfort operating in a consensus-driven Germanic "
            "corporate culture while driving urgency on "
            "software delivery"
        ),
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.MEDIUM,
        ),
    ),
]


@pytest.fixture()
def sample_requirements() -> list[Requirement]:
    """12 pre-built requirements matching the BMW CTO JD."""
    return [r.model_copy(deep=True) for r in _REQUIREMENTS]


# ---------------------------------------------------------------------------
# Pre-built rubric assessments (3 candidates x CV-assessable requirements)
# ---------------------------------------------------------------------------


def _build_rubric_assessments() -> list[RubricAssessment]:
    """Build rubric assessments for all candidates against CV-assessable reqs.

    Reflects candidate profiles:
    - Marcus: technical=exceeds, industry=gap, scope=exceeds, geo=partial
    - Sarah: industry=exceeds, technical=partial, leadership=exceeds
    - Kenji: balanced meets/partial, scope=gap, technical=meets
    """
    assessments: list[RubricAssessment] = []

    # ---- Marcus Chen ----
    _marcus_data: list[tuple[str, RubricLevel, Confidence, str | None, str | None]] = [
        (
            "REQ-01",
            RubricLevel.MEETS,
            Confidence.HIGH,
            ("PhD EE Stanford 2011, CTO Apex Robotics 2019-present, VP Eng Helion 2015-2019, Sr Dir Quanta 2011-2015"),
            None,
        ),
        (
            "REQ-02",
            RubricLevel.EXCEEDS,
            Confidence.HIGH,
            ("Full P&L responsibility for technology division (USD 620M annual budget)"),
            None,
        ),
        (
            "REQ-03",
            RubricLevel.EXCEEDS,
            Confidence.HIGH,
            ("Lead 320-person engineering organisation across San Francisco, Berlin, and Singapore"),
            None,
        ),
        (
            "REQ-04",
            RubricLevel.EXCEEDS,
            Confidence.HIGH,
            (
                "Architected SOA-based software-defined "
                "platform; built ADAS perception pipeline "
                "with lidar+camera fusion achieving L4"
            ),
            None,
        ),
        (
            "REQ-05",
            RubricLevel.EXCEEDS,
            Confidence.HIGH,
            (
                "Integrated two acquisitions (Navtiq Sensors, "
                "90 eng; StackEdge AI, 55 eng) -- unified "
                "toolchains within 8 months"
            ),
            None,
        ),
        (
            "REQ-06",
            RubricLevel.GAP,
            Confidence.HIGH,
            None,
            (
                "Career spans robotics, cloud, and semiconductor "
                "but not direct premium automotive OEM or "
                "tier-1 experience."
            ),
        ),
        (
            "REQ-07",
            RubricLevel.PARTIAL,
            Confidence.MEDIUM,
            ("Offices in SF, Berlin, Singapore -- EMEA/APAC presence but no China regulatory experience"),
            ("How deep was Marcus's involvement in APAC regulatory and data-localisation matters?"),
        ),
        (
            "REQ-08",
            RubricLevel.EXCEEDS,
            Confidence.HIGH,
            "PhD, Electrical Engineering -- Stanford (2011)",
            None,
        ),
        (
            "REQ-09",
            RubricLevel.PARTIAL,
            Confidence.MEDIUM,
            ("Languages: English (native), Mandarin (conversational) -- no German listed"),
            ("Has Marcus undertaken German language training or worked with German-speaking teams?"),
        ),
        (
            "REQ-10",
            RubricLevel.MEETS,
            Confidence.MEDIUM,
            ("Architected migration from monolithic embedded stack to SOA-based software-defined platform"),
            ("Was the Apex migration a multi-BU digital transformation or single-product re-architecture?"),
        ),
    ]

    for req_id, level, conf, citation, extra in _marcus_data:
        is_gap = level == RubricLevel.GAP
        is_partial = level == RubricLevel.PARTIAL
        assessments.append(
            RubricAssessment(
                requirement_id=req_id,
                candidate_name="Marcus Chen",
                rubric_level=level,
                confidence=conf,
                cv_citation=citation,
                cv_location=f"Marcus Chen CV -- {req_id}",
                notes=extra if is_gap else None,
                investigation_question=(extra if (is_partial or is_gap) and extra else None),
            )
        )

    # ---- Sarah Okafor ----
    _sarah_data: list[tuple[str, RubricLevel, Confidence, str | None, str | None]] = [
        (
            "REQ-01",
            RubricLevel.EXCEEDS,
            Confidence.HIGH,
            (
                "SVP Stellantis 2018-present, VP Continental "
                "2013-2018, Dir JLR 2007-2013 -- 18+ years "
                "automotive leadership"
            ),
            None,
        ),
        (
            "REQ-02",
            RubricLevel.MEETS,
            Confidence.HIGH,
            ("Full P&L ownership for digital services division (EUR 480M)"),
            ("EUR 480M is close to but slightly below USD 500M at current exchange rates."),
        ),
        (
            "REQ-03",
            RubricLevel.MEETS,
            Confidence.HIGH,
            ("Oversee 210-person technology organisation across Netherlands, Italy, and Morocco"),
            None,
        ),
        (
            "REQ-04",
            RubricLevel.PARTIAL,
            Confidence.MEDIUM,
            ("ADAS sensor-fusion at Continental; first hybrid-assist at JLR (Range Rover P400e)"),
            ("Strong legacy automotive (ICE, ADAS) but limited EV powertrain or SDV middleware depth."),
        ),
        (
            "REQ-05",
            RubricLevel.EXCEEDS,
            Confidence.HIGH,
            (
                "Led post-merger tech integration following "
                "PSA-FCA merger: harmonised 3 infotainment "
                "platforms within 18 months"
            ),
            None,
        ),
        (
            "REQ-06",
            RubricLevel.EXCEEDS,
            Confidence.HIGH,
            ("Stellantis (Maserati, Alfa Romeo, DS), Continental AG (tier-1 to BMW, MB, VW), JLR"),
            None,
        ),
        (
            "REQ-07",
            RubricLevel.PARTIAL,
            Confidence.MEDIUM,
            ("EMEA extensive; China via Continental Shanghai centre (45 engineers)"),
            ("APAC limited to single China centre. No Japan/Korea/ASEAN evidence."),
        ),
        (
            "REQ-08",
            RubricLevel.EXCEEDS,
            Confidence.HIGH,
            "MBA INSEAD (2007); MEng Loughborough (2002)",
            None,
        ),
        (
            "REQ-09",
            RubricLevel.EXCEEDS,
            Confidence.HIGH,
            ("English (native), German (professional fluency), French (business)"),
            None,
        ),
        (
            "REQ-10",
            RubricLevel.EXCEEDS,
            Confidence.HIGH,
            (
                "Enterprise-wide digital transformation "
                "spanning manufacturing, supply chain, CX "
                "across 11 BUs in EMEA and LatAm"
            ),
            None,
        ),
    ]

    for req_id, level, conf, citation, extra in _sarah_data:
        is_gap = level == RubricLevel.GAP
        is_partial = level == RubricLevel.PARTIAL
        assessments.append(
            RubricAssessment(
                requirement_id=req_id,
                candidate_name="Sarah Okafor",
                rubric_level=level,
                confidence=conf,
                cv_citation=citation,
                cv_location=f"Sarah Okafor CV -- {req_id}",
                notes=extra if is_gap else None,
                investigation_question=(extra if (is_partial or is_gap) and extra else None),
            )
        )

    # ---- Kenji Tanaka ----
    _kenji_data: list[tuple[str, RubricLevel, Confidence, str | None, str | None]] = [
        (
            "REQ-01",
            RubricLevel.MEETS,
            Confidence.HIGH,
            (
                "CTO Zenith 2020-present, Dir Toyota "
                "2015-2020, Sr Mgr Honda 2010-2015 -- "
                "15+ years automotive tech leadership"
            ),
            None,
        ),
        (
            "REQ-02",
            RubricLevel.GAP,
            Confidence.HIGH,
            None,
            ("Zenith division revenue EUR 95M -- significantly below USD 500M P&L threshold."),
        ),
        (
            "REQ-03",
            RubricLevel.GAP,
            Confidence.HIGH,
            None,
            ("Largest team: 85 engineers at Zenith. Well below the 200+ threshold."),
        ),
        (
            "REQ-04",
            RubricLevel.MEETS,
            Confidence.HIGH,
            ("AUTOSAR Adaptive middleware platform; EV BMS; ADAS camera-based features at Honda"),
            None,
        ),
        (
            "REQ-05",
            RubricLevel.PARTIAL,
            Confidence.LOW,
            ("No direct acquisition integration. Munich hub was greenfield, not post-M&A."),
            ("Has Kenji been involved in any M&A integration activities not on the CV?"),
        ),
        (
            "REQ-06",
            RubricLevel.MEETS,
            Confidence.HIGH,
            ("Toyota, Honda R&D, Zenith supplying to BMW and Porsche -- deep automotive pedigree"),
            None,
        ),
        (
            "REQ-07",
            RubricLevel.MEETS,
            Confidence.MEDIUM,
            ("Tokyo + Munich at Zenith; Toyota Japan + ASEAN; Honda global deployment"),
            ("APAC and EMEA evidence present but no China-specific experience."),
        ),
        (
            "REQ-08",
            RubricLevel.MEETS,
            Confidence.HIGH,
            "MS Computer Science -- University of Tokyo (2010)",
            None,
        ),
        (
            "REQ-09",
            RubricLevel.PARTIAL,
            Confidence.MEDIUM,
            ("Japanese (native), English (professional), German (intermediate)"),
            ("German intermediate -- may not meet professional fluency for Board interactions."),
        ),
        (
            "REQ-10",
            RubricLevel.MEETS,
            Confidence.MEDIUM,
            ("Transformed legacy hardware-centric culture to software-first agile delivery"),
            ("Transformation within single 85-person division, not multi-BU. Scale is a question."),
        ),
    ]

    for req_id, level, conf, citation, extra in _kenji_data:
        is_gap = level == RubricLevel.GAP
        is_partial = level == RubricLevel.PARTIAL
        assessments.append(
            RubricAssessment(
                requirement_id=req_id,
                candidate_name="Kenji Tanaka",
                rubric_level=level,
                confidence=conf,
                cv_citation=citation,
                cv_location=f"Kenji Tanaka CV -- {req_id}",
                notes=extra if is_gap else None,
                investigation_question=(extra if (is_partial or is_gap) and extra else None),
            )
        )

    return assessments


_RUBRIC_ASSESSMENTS: list[RubricAssessment] = _build_rubric_assessments()


@pytest.fixture()
def sample_rubric_assessments() -> list[RubricAssessment]:
    """Pre-built rubric assessments for 3 candidates x 10 CV-assessable reqs."""
    return [a.model_copy(deep=True) for a in _RUBRIC_ASSESSMENTS]


# ---------------------------------------------------------------------------
# Scenario config
# ---------------------------------------------------------------------------

_SCENARIO_CONFIG = ScenarioConfig(
    name=ScenarioName.DIGITAL_TRANSFORMATION,
    category_weights={
        "EXECUTION": 1.0,
        "STRATEGIC": 1.2,
        "COLLISION": 0.8,
        "COMPLEMENT": 0.9,
        "FRICTION": 1.0,
        "CULTURAL": 1.1,
        "DERAILMENT": 1.3,
        "DARK_SIDE": 1.2,
        "INTEGRATION": 1.1,
        "TENURE": 0.7,
        "GROUPTHINK": 0.8,
        "EXPERIENCE_STRENGTH": 1.0,
        "EXPERIENCE_GAP": 1.2,
        "EVIDENCE_QUALITY": 0.9,
        "ROUTING": 0.5,
    },
)


@pytest.fixture()
def sample_scenario_config() -> ScenarioConfig:
    """ScenarioConfig for digital_transformation scenario."""
    return _SCENARIO_CONFIG.model_copy(deep=True)
