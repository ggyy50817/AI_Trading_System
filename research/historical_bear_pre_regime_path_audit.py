"""
Historical BEAR Pre-Regime Path Audit V1

Measure BTC price movement before the first BEAR
bucket of a historical BEAR episode.

Research only:
- No live trading
- No Strategy A modification
- No automatic parameter changes
- Historical closed-candle data only
"""

from __future__ import annotations

from typing import Any


WINDOWS = (
    (1, "15m"),
    (3, "45m"),
    (6, "90m"),
    (12, "3h"),
)


def backward_return(
    closes: list[float],
    current_index: int,
    candles: int,
) -> float:
    """
    Percentage BTC return from N candles before
    the current candle to the current candle.

    Negative = BTC had fallen before BEAR detection.
    Positive = BTC had risen before BEAR detection.
    """

    if candles < 1:
        raise ValueError(
            "candles must be >= 1"
        )

    if current_index < 0:
        raise ValueError(
            "current_index must be >= 0"
        )

    previous_index = (
        current_index - candles
    )

    if previous_index < 0:
        raise ValueError(
            "Insufficient previous candles"
        )

    start = float(
        closes[previous_index]
    )

    end = float(
        closes[current_index]
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


def make_path_stats() -> dict[str, Any]:
    return {
        "n": 0,
        "up": 0,
        "down": 0,
        "flat": 0,
        "return_sum": 0.0,
    }


def update_path_stats(
    stats: dict[str, Any],
    value: float,
) -> None:

    stats["n"] += 1
    stats["return_sum"] += value

    move = direction(
        value
    )

    if move == "UP":
        stats["up"] += 1

    elif move == "DOWN":
        stats["down"] += 1

    else:
        stats["flat"] += 1


def path_summary(
    stats: dict[str, Any],
) -> dict[str, Any]:

    n = int(
        stats["n"]
    )

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
            stats["up"]
            / n
            * 100.0
        ),
        "down_pct": (
            stats["down"]
            / n
            * 100.0
        ),
        "flat_pct": (
            stats["flat"]
            / n
            * 100.0
        ),
        "avg_return": (
            stats["return_sum"]
            / n
        ),
    }
