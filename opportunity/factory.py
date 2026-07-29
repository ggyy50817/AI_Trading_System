"""
Opportunity Factory V1

Factory for creating OpportunityRecord objects.

Responsibilities

- Convert scanner results into OpportunityRecord.
- Create ONE OpportunityRecord per completed scanner analysis.
- No logging.
- No trading.
- No API calls.
- No business logic.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from core.opportunity_record import OpportunityRecord


def create_opportunity(
    *,
    symbol: str,
    market_regime: str,
    long_score: int,
    short_score: int,
    long_threshold: int,
    short_threshold: int,
    can_long: bool,
    can_short: bool,
    reason: str | None = None,
    context: dict[str, Any] | None = None,
    source: str = "scanner",
) -> OpportunityRecord:
    """
    Create one OpportunityRecord.

    This function performs object creation only.
    """

    return OpportunityRecord(
        timestamp=datetime.now(),
        source=source,
        symbol=symbol,
        market_regime=market_regime,
        long_score=long_score,
        short_score=short_score,
        long_threshold=long_threshold,
        short_threshold=short_threshold,
        can_long=can_long,
        can_short=can_short,
        reason=reason,
        context=context,
    )