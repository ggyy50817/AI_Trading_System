"""
Historical Regime Direction Diagnostic V1

Investigate why historical Shadow direction performance
can appear opposite to BTC Market Regime direction.

Research only:
- No live trading
- No Strategy A modification
- No automatic parameter changes
- Historical closed-candle data only
- Strict anti-lookahead boundary
"""

from __future__ import annotations

from typing import Any


def pct_distance(
    value: float,
    reference: float,
) -> float:
    """
    Return percentage distance from reference.
    """

    if reference == 0:
        return 0.0

    return (
        (value - reference)
        / reference
        * 100.0
    )


def sequence_return(
    sequence: list[dict[str, Any]],
    candles: int,
) -> float:
    """
    Return BTC percentage move across the requested
    number of historical closed candles.

    Positive = BTC moved up.
    Negative = BTC moved down.
    """

    if candles < 1:
        raise ValueError(
            "candles must be >= 1"
        )

    if len(sequence) <= candles:
        raise ValueError(
            "Insufficient sequence length"
        )

    start = float(
        sequence[-candles - 1][
            "latest_close"
        ]
    )

    end = float(
        sequence[-1][
            "latest_close"
        ]
    )

    return pct_distance(
        end,
        start,
    )
def momentum_direction(
    value: float,
) -> str:
    """
    Convert BTC return into directional label.
    """

    if value > 0:
        return "UP"

    if value < 0:
        return "DOWN"

    return "FLAT"


def make_performance_stats() -> dict[str, Any]:
    """
    Create an empty performance accumulator.
    """

    return {
        "n": 0,
        "wins": 0,
        "losses": 0,
        "pnl": 0.0,
        "gross_profit": 0.0,
        "gross_loss": 0.0,
    }


def update_performance_stats(
    stats: dict[str, Any],
    pnl: float,
) -> None:
    """
    Add one Shadow outcome to performance stats.
    """

    stats["n"] += 1
    stats["pnl"] += pnl

    if pnl > 0:
        stats["wins"] += 1
        stats["gross_profit"] += pnl

    elif pnl < 0:
        stats["losses"] += 1
        stats["gross_loss"] += pnl


def performance_summary(
    stats: dict[str, Any],
) -> dict[str, float | int | str]:
    """
    Calculate derived performance metrics.
    """

    n = int(stats["n"])
    wins = int(stats["wins"])
    losses = int(stats["losses"])

    pnl = float(stats["pnl"])
    gross_profit = float(
        stats["gross_profit"]
    )
    gross_loss = float(
        stats["gross_loss"]
    )

    win_rate = (
        wins / n * 100.0
        if n
        else 0.0
    )

    expectancy = (
        pnl / n
        if n
        else 0.0
    )

    gross_loss_abs = abs(
        gross_loss
    )

    if gross_loss_abs > 0:
        profit_factor: float | str = (
            gross_profit
            / gross_loss_abs
        )
    elif gross_profit > 0:
        profit_factor = "INF"
    else:
        profit_factor = 0.0

    return {
        "n": n,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "pnl": pnl,
        "expectancy": expectancy,
        "profit_factor": profit_factor,
    }
