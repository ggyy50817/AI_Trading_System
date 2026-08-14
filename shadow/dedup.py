"""
Shadow Opportunity Dedup V1

Prevent repeated scanner cycles from creating duplicate ShadowTrade samples
for the same continuous trading opportunity.

A continuous opportunity is identified by:

    symbol + side + AI score + threshold + market regime

If the same opportunity remains active across scanner cycles,
only the first observation is accepted.

When the opportunity changes, a new ShadowTrade may be accepted.

Research / observation only.
No exchange orders.
No API calls.
"""

from __future__ import annotations


_active_opportunities: dict[str, tuple] = {}


def build_opportunity_signature(
    symbol,
    side,
    ai_score,
    threshold,
    market_regime,
):
    """
    Build the identity of one Shadow opportunity.
    """

    return (
        str(side),
        float(ai_score),
        float(threshold),
        str(market_regime),
    )


def is_new_shadow_opportunity(
    symbol,
    side,
    ai_score,
    threshold,
    market_regime,
):
    """
    Return True only when the opportunity differs from the last
    accepted opportunity for this symbol.

    The first opportunity for a symbol is always accepted.
    """

    symbol = str(symbol)

    signature = build_opportunity_signature(
        symbol=symbol,
        side=side,
        ai_score=ai_score,
        threshold=threshold,
        market_regime=market_regime,
    )

    previous_signature = _active_opportunities.get(symbol)

    if previous_signature == signature:
        return False

    _active_opportunities[symbol] = signature

    return True


def clear_shadow_opportunity(symbol):
    """
    Forget the active opportunity for one symbol.
    """

    _active_opportunities.pop(str(symbol), None)


def clear_all_shadow_opportunities():
    """
    Reset all in-memory Shadow opportunity state.
    """

    _active_opportunities.clear()