"""
Historical Regime Threshold Sensitivity V1

Test alternative Market Regime thresholds against
historical Shadow trade outcomes.

Research only:
- No live trading
- No Strategy A modification
- No automatic parameter changes
- Historical closed-candle data only
"""

from __future__ import annotations

from itertools import product


VOLUME_THRESHOLDS = [
    0.8,
    0.7,
    0.6,
    0.5,
    0.0,
]

SLOPE_THRESHOLDS = [
    0.0010,
    0.0008,
    0.0005,
    0.0003,
    0.0,
]


def classify_with_thresholds(
    snapshot: dict,
    volume_threshold: float,
    slope_threshold: float,
) -> str:
    latest_close = float(snapshot["latest_close"])
    ma20 = float(snapshot["ma20"])
    ma60 = float(snapshot["ma60"])
    atr_pct = float(snapshot["atr_pct"])
    volume_ratio = float(snapshot["volume_ratio"])
    ma20_slope = float(snapshot["ma20_slope"])

    # Keep current ATR rule unchanged.
    if atr_pct > 0.035:
        return "RANGE"

    if volume_ratio < volume_threshold:
        return "RANGE"

    if abs(ma20_slope) < latest_close * slope_threshold:
        return "RANGE"

    if latest_close > ma20 and ma20 > ma60:
        return "BULL"

    if latest_close < ma20 and ma20 < ma60:
        return "BEAR"

    return "RANGE"


def iter_threshold_combinations():
    return product(
        VOLUME_THRESHOLDS,
        SLOPE_THRESHOLDS,
    )
