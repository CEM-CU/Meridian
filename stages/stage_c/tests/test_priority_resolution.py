"""Tests for C2: Active Priority Resolution."""

from shared.models import Priority, Requirement, ScenarioConfig, ScenarioName, ScenarioPriority
from stage_c.priority_resolution import resolve_active_priorities


def _make_scenario_priority(
    digital_transformation: Priority = Priority.MEDIUM,
    post_acquisition: Priority = Priority.MEDIUM,
    turnaround: Priority = Priority.MEDIUM,
    stabilization: Priority = Priority.MEDIUM,
    growth: Priority = Priority.MEDIUM,
) -> ScenarioPriority:
    """Helper: build a ScenarioPriority with convenient defaults."""
    return ScenarioPriority(
        digital_transformation=digital_transformation,
        post_acquisition=post_acquisition,
        turnaround=turnaround,
        stabilization=stabilization,
        growth=growth,
    )


def _make_requirement(
    requirement_id: str = "REQ-01",
    text: str = "Lead digital transformation programmes",
    source_quote: str = "Lead digital transformation programmes",
    assessable_from_cv: bool = True,
    scenario_priority: ScenarioPriority | None = None,
) -> Requirement:
    """Helper: build a Requirement with convenient defaults."""
    if scenario_priority is None:
        scenario_priority = _make_scenario_priority()
    return Requirement(
        requirement_id=requirement_id,
        text=text,
        source_quote=source_quote,
        assessable_from_cv=assessable_from_cv,
        scenario_priority=scenario_priority,
    )


class TestResolveActivePrioritiesEmpty:
    def test_empty_requirements_returns_empty(self) -> None:
        """Empty input list produces empty output."""
        scenario = ScenarioConfig(name=ScenarioName.GROWTH)
        result = resolve_active_priorities([], scenario)
        assert result == []


class TestResolveActivePrioritiesCV:
    def test_cv_assessable_requirement_gets_correct_priority(self) -> None:
        """A CV-assessable requirement resolves to the scenario's priority."""
        sp = _make_scenario_priority(
            digital_transformation=Priority.HIGH,
            turnaround=Priority.LOW,
        )
        req = _make_requirement(assessable_from_cv=True, scenario_priority=sp)
        scenario = ScenarioConfig(name=ScenarioName.DIGITAL_TRANSFORMATION)
        result = resolve_active_priorities([req], scenario)
        assert len(result) == 1
        assert result[0] == (req, Priority.HIGH)

    def test_different_scenario_yields_different_priority(self) -> None:
        """Same requirement resolves to different priorities for different scenarios."""
        sp = _make_scenario_priority(
            digital_transformation=Priority.HIGH,
            turnaround=Priority.LOW,
        )
        req = _make_requirement(assessable_from_cv=True, scenario_priority=sp)

        result_dt = resolve_active_priorities([req], ScenarioConfig(name=ScenarioName.DIGITAL_TRANSFORMATION))
        result_ta = resolve_active_priorities([req], ScenarioConfig(name=ScenarioName.TURNAROUND))

        assert result_dt[0][1] == Priority.HIGH
        assert result_ta[0][1] == Priority.LOW

    def test_all_cv_assessable_requirements_get_valid_priorities(self) -> None:
        """All CV-assessable requirements in output have a valid Priority value."""
        requirements = [
            _make_requirement(
                requirement_id=f"REQ-{i:02d}",
                text=f"Requirement {i}",
                source_quote=f"Source {i}",
                assessable_from_cv=True,
                scenario_priority=_make_scenario_priority(growth=Priority(p)),
            )
            for i, p in enumerate(["high", "medium", "low"], start=1)
        ]
        scenario = ScenarioConfig(name=ScenarioName.GROWTH)
        result = resolve_active_priorities(requirements, scenario)

        assert len(result) == 3
        priorities = [priority for _, priority in result]
        assert priorities == [Priority.HIGH, Priority.MEDIUM, Priority.LOW]
        for priority in priorities:
            assert isinstance(priority, Priority)


class TestResolveActivePrioritiesBehavioral:
    def test_behavioral_requirement_gets_none_priority(self) -> None:
        """Behavioral requirement (assessable_from_cv=False) gets priority=None."""
        req = _make_requirement(assessable_from_cv=False)
        scenario = ScenarioConfig(name=ScenarioName.STABILIZATION)
        result = resolve_active_priorities([req], scenario)
        assert len(result) == 1
        assert result[0] == (req, None)

    def test_behavioral_requirement_none_regardless_of_scenario(self) -> None:
        """Behavioral requirement always yields None regardless of active scenario."""
        req = _make_requirement(assessable_from_cv=False)
        for scenario_name in ScenarioName:
            result = resolve_active_priorities([req], ScenarioConfig(name=scenario_name))
            assert result[0][1] is None, f"Expected None for scenario {scenario_name}"


class TestResolveActivePrioritiesMixed:
    def test_mixed_requirements_preserve_order_and_correct_priorities(self) -> None:
        """Mixed CV and behavioral requirements produce correct priority pairing in order."""
        sp_high = _make_scenario_priority(post_acquisition=Priority.HIGH)
        sp_low = _make_scenario_priority(post_acquisition=Priority.LOW)

        cv_req_1 = _make_requirement(
            requirement_id="REQ-01",
            text="Post-acquisition integration track record",
            source_quote="Post-acquisition integration track record",
            assessable_from_cv=True,
            scenario_priority=sp_high,
        )
        behavioral_req = _make_requirement(
            requirement_id="REQ-02",
            text="Inspirational leadership style",
            source_quote="Inspirational leadership style",
            assessable_from_cv=False,
            scenario_priority=_make_scenario_priority(),
        )
        cv_req_2 = _make_requirement(
            requirement_id="REQ-03",
            text="Experience with agile methodologies",
            source_quote="Experience with agile methodologies",
            assessable_from_cv=True,
            scenario_priority=sp_low,
        )

        scenario = ScenarioConfig(name=ScenarioName.POST_ACQUISITION)
        result = resolve_active_priorities([cv_req_1, behavioral_req, cv_req_2], scenario)

        assert len(result) == 3
        assert result[0] == (cv_req_1, Priority.HIGH)
        assert result[1] == (behavioral_req, None)
        assert result[2] == (cv_req_2, Priority.LOW)

    def test_output_length_matches_input_length(self) -> None:
        """Output has exactly one entry per input requirement."""
        requirements = [
            _make_requirement(
                requirement_id=f"REQ-{i:02d}",
                text=f"Req {i}",
                source_quote=f"Req {i}",
                assessable_from_cv=i % 2 == 0,
            )
            for i in range(1, 7)
        ]
        scenario = ScenarioConfig(name=ScenarioName.GROWTH)
        result = resolve_active_priorities(requirements, scenario)
        assert len(result) == len(requirements)

    def test_requirement_objects_are_preserved_unchanged(self) -> None:
        """The Requirement objects in output are the same objects as the input."""
        reqs = [
            _make_requirement(requirement_id="REQ-01", assessable_from_cv=True),
            _make_requirement(
                requirement_id="REQ-02",
                text="Behavioral trait",
                source_quote="Behavioral trait",
                assessable_from_cv=False,
            ),
        ]
        scenario = ScenarioConfig(name=ScenarioName.DIGITAL_TRANSFORMATION)
        result = resolve_active_priorities(reqs, scenario)
        for (out_req, _), in_req in zip(result, reqs, strict=True):
            assert out_req is in_req
