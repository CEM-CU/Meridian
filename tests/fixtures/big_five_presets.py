"""Big Five archetype presets for testing personality-flag derivation.

Five archetypes spanning common C-suite personality profiles. Each maps to a
BigFiveScores instance with OCEAN values on a 0.0-1.0 scale:
- very low: 0.15-0.25
- low: 0.25-0.40
- medium: 0.45-0.55
- high: 0.65-0.80
- very high: 0.85-0.95
"""

from meridian.models import BigFiveScores

BIG_FIVE_PRESETS: dict[str, BigFiveScores] = {
    "The Turnaround Driver": BigFiveScores(
        O=0.50,  # medium — pragmatic, not wedded to novel ideas
        C=0.82,  # high — disciplined, structured execution
        E=0.75,  # high — assertive, energises teams through crisis
        A=0.30,  # low — willing to make unpopular decisions
        N=0.25,  # low — calm under intense pressure
    ),
    "The Innovation Catalyst": BigFiveScores(
        O=0.92,  # very high — thrives on novelty, exploratory
        C=0.50,  # medium — enough discipline to ship, not rigid
        E=0.72,  # high — evangelises ideas, builds coalitions
        A=0.48,  # medium — collaborative but challenges orthodoxy
        N=0.22,  # low — emotionally stable during uncertainty
    ),
    "The Steady Operator": BigFiveScores(
        O=0.20,  # low — conservative, risk-averse
        C=0.90,  # very high — meticulous, process-driven
        E=0.50,  # medium — competent communicator, not flashy
        A=0.70,  # high — harmonious, builds trust through reliability
        N=0.48,  # medium — occasional worry but functional
    ),
    "The Transformational Leader": BigFiveScores(
        O=0.78,  # high — embraces change, future-focused
        C=0.75,  # high — balances vision with follow-through
        E=0.80,  # high — charismatic, inspires large organisations
        A=0.35,  # low — challenges consensus when needed
        N=0.20,  # low — resilient under sustained pressure
    ),
    "The Collaborative Builder": BigFiveScores(
        O=0.52,  # medium — open but grounded
        C=0.50,  # medium — flexible, adapts to team needs
        E=0.48,  # medium — listens as much as speaks
        A=0.88,  # very high — empathetic, consensus-seeking
        N=0.28,  # low — emotionally steady, supportive presence
    ),
}
