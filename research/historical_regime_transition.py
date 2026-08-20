"""
Historical Regime Transition V1

Measure the age of the current historical BTC market regime.

Research only:
- No live trading
- No Strategy A modification
- No automatic parameter changes
- Historical closed-candle data only
"""

from __future__ import annotations

from typing import Any, Callable

from research.historical_market_regime import (
    classify_historical_regime,
)


def calculate_regime_age(
    sequence: list[dict[str, Any]],
    classifier: Callable[
        [dict[str, Any]],
        str,
    ] = classify_historical_regime,
) -> tuple[str, int, bool]:
    """
    Return:
        current_regime
        consecutive candle count
        left_censored

    left_censored=True means the current regime extends
    to the oldest candle available in the sequence, so
    the exact regime age is unknown.
    """

    if not sequence:
        raise ValueError(
            "Historical context sequence is empty"
        )

    regimes = [
        classifier(snapshot)
        for snapshot in sequence
    ]

    current_regime = regimes[-1]
    age = 1

    for regime in reversed(regimes[:-1]):
        if regime != current_regime:
            break

        age += 1

    left_censored = (
        age == len(regimes)
    )

    return (
        current_regime,
        age,
        left_censored,
    )


def regime_age_bucket(
    age: int,
    left_censored: bool = False,
) -> str:
    """
    Convert regime age into a research bucket.
    """

    if age < 1:
        raise ValueError(
            "Regime age must be >= 1"
        )

    if left_censored:
        return f"{age}+"

    if age == 1:
        return "1"

    if age <= 3:
        return "2-3"

    if age <= 8:
        return "4-8"

    if age <= 20:
        return "9-20"

    if age <= 40:
        return "21-40"

    if age <= 79:
        return "41-79"

    return "80+"
