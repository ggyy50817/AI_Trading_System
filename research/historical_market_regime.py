"""
Historical Market Regime Classifier V1

Classify historical BTC market regime from a
Historical Context Snapshot.

Research only:
- No live trading
- No Strategy A modification
- No automatic parameter changes
"""

from __future__ import annotations

from typing import Any


def classify_historical_regime(
    snapshot: dict[str, Any],
) -> str:
    """
    Reproduce Market Regime V1 classification
    using an already reconstructed historical snapshot.
    """

    latest_close = float(
        snapshot["latest_close"]
    )

    latest_ma20 = float(
        snapshot["ma20"]
    )

    latest_ma60 = float(
        snapshot["ma60"]
    )

    atr_pct = float(
        snapshot["atr_pct"]
    )

    volume_ratio = float(
        snapshot["volume_ratio"]
    )

    ma20_slope = float(
        snapshot["ma20_slope"]
    )

    if atr_pct > 0.035:
        return "RANGE"

    if volume_ratio < 0.8:
        return "RANGE"

    if abs(ma20_slope) < latest_close * 0.001:
        return "RANGE"

    if (
        latest_close > latest_ma20
        and latest_ma20 > latest_ma60
    ):
        return "BULL"

    if (
        latest_close < latest_ma20
        and latest_ma20 < latest_ma60
    ):
        return "BEAR"

    return "RANGE"