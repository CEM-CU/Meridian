# Stage D — Implementation Notes

> last_updated: 2026-03-29T00:00:00Z by human (bootstrap)

## Module Structure

```
stages/stage_d/src/stage_d/
├── __init__.py
├── personality_flags.py    # D1: Big Five → personality flags (threshold logic)
├── cv_validation.py        # D2: validate CV flags from C4
├── merge.py                # D3: concatenate both streams
├── validation.py           # D4: 5 validation checks
├── mode.py                 # D5: assessment mode determination
├── pipeline.py             # D1→D6 orchestration, produces StageDOutput
└── config/
    ├── thresholds.py       # scenario × dimension → threshold values (data, not logic)
    ├── flag_vocabulary.py  # canonical flag names, categories, valence, topic_keywords
    └── contradictions.py   # contradiction pairs (unconditional + conditional)
```

## Threshold Configuration

Store thresholds as a nested dict, not hardcoded if-else chains. Structure:

```
THRESHOLDS = {
    "digital_transformation": {
        "O": [
            {"flag": "STRATEGIC_OPENNESS_FIT", "threshold": 0.65, "direction": "above", "category": "STRATEGIC", "valence": "positive"},
            {"flag": "STRATEGIC_LOW_OPENNESS_RISK", "threshold": 0.35, "direction": "below", "category": "STRATEGIC", "valence": "negative"},
        ],
        "C": [...],
    },
    "turnaround": {...},
}
```

This makes the entire derivation logic data-driven. Adding a new flag = adding a dict entry. Changing a threshold = changing a number. No logic changes needed.

## Canonical Flag Vocabulary

Define ALL valid flag names in one file (`flag_vocabulary.py`). This is the reference that Stage E's audit checks against. Include for each flag: name, category, valence, evidence_type, required_fields, topic_keywords. Both personality-derived and CV-derived flags live here.

CV-derived flag names are now generic: CV_GAP, CV_PARTIAL, CV_EXCEEDS, CV_BEHAVIORAL_ROUTED, CV_LOW_CONFIDENCE_CLUSTER, CV_SYSTEMATIC_GAP. No specialized variants (CV_SCOPE_GAP, CV_INDUSTRY_MISMATCH etc. are gone). The requirement text on the flag carries the domain context. The priority metadata (from requirement.scenario_priority) determines weight downstream.

The vocabulary is the immune system — if a flag name isn't in the vocabulary, it doesn't exist.

## Key Invariants

- Stage D output flag count == personality_flag_count + cv_flag_count (provenance matches reality)
- Every flag in output exists in canonical vocabulary
- No candidate has contradictory flags after validation
- partial mode → personality_flag_count == 0 for that candidate
- Every CV flag.requirement_id references a requirement in confirmed_requirements
- StageDOutput.scenario == input StageCOutput.scenario (pass-through, not transformed)
