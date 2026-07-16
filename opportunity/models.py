"""Opportunity data models.

Opportunity Logger V1
    Uses ``dict[str, Any]`` as the opportunity payload. No typed model is
    required yet; callers pass plain dictionaries to ``log_opportunity``.

Future (V2)
    Introduce an ``OpportunityRecord`` dataclass as the canonical schema.

    Planned fields:
        - timestamp
        - symbol
        - side
        - price
        - ai_score
        - long_score
        - short_score
        - market_regime
        - reason
        - skip_reason
        - executed

    Planned consumers / use cases:
        - Shadow Trading
        - Decision Dataset
        - Replay Learning
"""
