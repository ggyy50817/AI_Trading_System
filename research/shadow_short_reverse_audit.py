"""
Shadow SHORT Reverse Audit V1.

Research only. No exchange orders.
"""

from __future__ import annotations

from copy import deepcopy
from math import isfinite

from replay.shadow_outcome_engine import simulate_shadow_outcome


def is_score_eligible_short(record: dict) -> bool:
    """Check recorded SHORT score threshold only."""

    if record.get("side") != "SHORT":
        return False

    try:
        score = float(record["ai_score"])
        threshold = float(record["threshold"])
    except (KeyError, TypeError, ValueError):
        return False

    return (
        isfinite(score)
        and isfinite(threshold)
        and threshold > 0
        and score >= threshold
    )


def build_reverse_pair(record: dict) -> tuple[dict, dict]:
    """Create independent SHORT and reverse LONG records."""

    if not is_score_eligible_short(record):
        raise ValueError("Not a score-eligible SHORT candidate")

    original = deepcopy(record)
    reverse = deepcopy(record)

    original["side"] = "SHORT"
    reverse["side"] = "LONG"

    original["signal_side"] = "SHORT"
    reverse["signal_side"] = "SHORT"

    original["experiment"] = "ORIGINAL_SHORT"
    reverse["experiment"] = "REVERSE_LONG"

    return original, reverse


def simulate_reverse_pair(
    record: dict,
    future_klines,
    notional: float = 100.0,
) -> dict:
    """Replay both sides using identical future candles."""

    original, reverse = build_reverse_pair(record)

    original_result = simulate_shadow_outcome(
        original,
        future_klines,
        notional,
    )

    reverse_result = simulate_shadow_outcome(
        reverse,
        future_klines,
        notional,
    )

    return {
        "symbol": record.get("symbol"),
        "timestamp": record.get("timestamp"),
        "ai_score": record.get("ai_score"),
        "threshold": record.get("threshold"),
        "market_regime": record.get("market_regime"),
        "eligibility": "SCORE_ONLY",
        "original_short": original_result,
        "reverse_long": reverse_result,
        "pnl_difference": (
            reverse_result["realized_pnl"]
            - original_result["realized_pnl"]
        ),
    }
