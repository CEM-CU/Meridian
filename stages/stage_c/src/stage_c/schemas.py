"""OpenAI-compatible JSON schemas for structured output in Stage C.

These schemas are passed as ``response_format`` to force the LLM to return
strictly valid JSON matching our Pydantic models. Only used with models that
support structured outputs (OpenAI gpt-4.1+, etc.). Other models ignore them.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# C1: JD Requirement Extraction — array of Requirement objects
# ---------------------------------------------------------------------------

C1_REQUIREMENTS_SCHEMA: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "requirements_extraction",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "requirements": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "requirement_id": {"type": "string"},
                            "text": {"type": "string"},
                            "source_quote": {"type": "string"},
                            "assessable_from_cv": {"type": "boolean"},
                            "scenario_priority": {
                                "type": "object",
                                "properties": {
                                    "digital_transformation": {"type": "string", "enum": ["high", "medium", "low"]},
                                    "post_acquisition": {"type": "string", "enum": ["high", "medium", "low"]},
                                    "turnaround": {"type": "string", "enum": ["high", "medium", "low"]},
                                    "stabilization": {"type": "string", "enum": ["high", "medium", "low"]},
                                    "growth": {"type": "string", "enum": ["high", "medium", "low"]},
                                },
                                "required": [
                                    "digital_transformation",
                                    "post_acquisition",
                                    "turnaround",
                                    "stabilization",
                                    "growth",
                                ],
                                "additionalProperties": False,
                            },
                        },
                        "required": [
                            "requirement_id",
                            "text",
                            "source_quote",
                            "assessable_from_cv",
                            "scenario_priority",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["requirements"],
            "additionalProperties": False,
        },
    },
}

# ---------------------------------------------------------------------------
# C3: CV Rubric Assessment — array of RubricAssessment objects
# ---------------------------------------------------------------------------

C3_ASSESSMENTS_SCHEMA: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "cv_rubric_assessments",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "assessments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "requirement_id": {"type": "string"},
                            "candidate_name": {"type": "string"},
                            "rubric_level": {
                                "type": "string",
                                "enum": ["exceeds", "meets", "partial", "gap", "not_assessable"],
                            },
                            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                            "cv_citation": {"type": ["string", "null"]},
                            "cv_location": {"type": ["string", "null"]},
                            "notes": {"type": ["string", "null"]},
                            "investigation_question": {"type": ["string", "null"]},
                        },
                        "required": [
                            "requirement_id",
                            "candidate_name",
                            "rubric_level",
                            "confidence",
                            "cv_citation",
                            "cv_location",
                            "notes",
                            "investigation_question",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["assessments"],
            "additionalProperties": False,
        },
    },
}
