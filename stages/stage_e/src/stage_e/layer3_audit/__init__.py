"""Layer 3 Audit — E5.

Public API: run_audit (runner), individual check functions (checks).
"""

from stage_e.layer3_audit.checks import (
    check_biographical_references,
    check_downweight_ratio,
    check_flag_scope,
    check_hallucinated_references,
    check_research_general_cap,
    check_schema_validity,
    check_semantic_drift,
    check_unaddressed_flags,
)
from stage_e.layer3_audit.runner import run_audit

__all__ = [
    "check_biographical_references",
    "check_downweight_ratio",
    "check_flag_scope",
    "check_hallucinated_references",
    "check_research_general_cap",
    "check_schema_validity",
    "check_semantic_drift",
    "check_unaddressed_flags",
    "run_audit",
]
