"""
Historical Regime Semantic Audit V1

Validate the directional meaning of historical BTC
regime labels using future BTC returns.

Research only:
- No live trading
- No Strategy A modification
- No automatic parameter changes
- Historical analysis only
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


WINDOWS = (
    (1, "15m"),
    (3, "45m"),
    (6, "90m"),
    (12, "3h"),
)


def future_return(
    closes: list[float],
    current_index: int,
    candles: int,
) -> float:
    """
    Percentage return from the current close to a
    future close N candles later.

    Positive = BTC rose after the classified candle.
    Negative = BTC fell after the classified candle.
    """

    if candles < 1:
        raise ValueError(
            "candles must be >= 1"
        )

    future_index = (
        current_index + candles
    )

    if current_index < 0:
        raise ValueError(
            "current_index must be >= 0"
        )

    if future_index >= len(closes):
        raise ValueError(
            "Insufficient future candles"
        )

    start = float(
        closes[current_index]
    )

    end = float(
        closes[future_index]
    )

    if start == 0:
        raise ValueError(
            "Start close cannot be zero"
        )

    return (
        (end - start)
        / start
        * 100.0
    )


def direction(
    value: float,
) -> str:
    if value > 0:
        return "UP"

    if value < 0:
        return "DOWN"

    return "FLAT"


def make_semantic_stats() -> dict[str, Any]:
    return {
        "n": 0,
        "up": 0,
        "down": 0,
        "flat": 0,
        "return_sum": 0.0,
        "returns": [],
    }


def update_semantic_stats(
    stats: dict[str, Any],
    value: float,
) -> None:

    stats["n"] += 1
    stats["return_sum"] += value
    stats["returns"].append(value)

    move = direction(value)

    if move == "UP":
        stats["up"] += 1
    elif move == "DOWN":
        stats["down"] += 1
    else:
        stats["flat"] += 1


def semantic_summary(
    stats: dict[str, Any],
) -> dict[str, Any]:

    n = int(stats["n"])

    if n == 0:
        return {
            "n": 0,
            "up_pct": 0.0,
            "down_pct": 0.0,
            "flat_pct": 0.0,
            "avg_return": 0.0,
        }

    return {
        "n": n,
        "up_pct": (
            stats["up"] / n * 100.0
        ),
        "down_pct": (
            stats["down"] / n * 100.0
        ),
        "flat_pct": (
            stats["flat"] / n * 100.0
        ),
        "avg_return": (
            stats["return_sum"] / n
        ),
    }
