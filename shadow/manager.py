"""
Shadow Manager V1

Create virtual shadow trades.

No validation yet.
"""

from datetime import datetime

from core.shadow_trade import ShadowTrade


def create_shadow_trade(
    *,
    symbol: str,
    side: str,
    entry_price: float,
) -> ShadowTrade:

    return ShadowTrade(
        created_at=datetime.now(),
        symbol=symbol,
        side=side,
        entry_price=entry_price,
    )