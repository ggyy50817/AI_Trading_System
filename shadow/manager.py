"""
Shadow Manager V1

Create virtual shadow trades from OpportunityRecord objects.

Responsibilities

- Receive OpportunityRecord.
- Select a virtual LONG or SHORT candidate.
- Create ShadowTrade objects.
- Never submit exchange orders.
- Never modify live trading logic.
- No API calls.

Shadow Trading is observation/research only.
"""

from __future__ import annotations

from core.opportunity_record import OpportunityRecord
from core.shadow_trade import ShadowTrade


def create_shadow_trade(opportunity: OpportunityRecord) -> ShadowTrade | None:
    """
    Convert one OpportunityRecord into one ShadowTrade candidate.

    Selection rules:
    - Use the higher AI score as the shadow direction.
    - If LONG and SHORT scores are equal, skip the opportunity.
    - Entry price is read from the selected side's latest_close.
    - Missing or invalid price means no ShadowTrade is created.

    IMPORTANT:
    Shadow selection does NOT require the real trading threshold to pass.
    This allows rejected opportunities to be studied safely.
    """

    if opportunity.long_score == opportunity.short_score:
        return None

    if opportunity.long_score > opportunity.short_score:
        side = "LONG"
        ai_score = opportunity.long_score
        threshold = opportunity.long_threshold
        context_key = "long"
    else:
        side = "SHORT"
        ai_score = opportunity.short_score
        threshold = opportunity.short_threshold
        context_key = "short"

    context = opportunity.context or {}
    side_context = context.get(context_key, {})

    if not isinstance(side_context, dict):
        return None

    entry_price = side_context.get("latest_close")

    if entry_price is None:
        return None

    try:
        entry_price = float(entry_price)
    except (TypeError, ValueError):
        return None

    if entry_price <= 0:
        return None

    return ShadowTrade(
        created_at=opportunity.timestamp,
        symbol=opportunity.symbol,
        side=side,
        entry_price=entry_price,
        ai_score=ai_score,
        threshold=threshold,
        market_regime=opportunity.market_regime,
    )