"""
Large Historical Regime Dataset V1

Build a large-sample historical BTC regime timeline
from paginated historical Kline data.

Research only:
- No live trading
- No Strategy A modification
- No automatic parameter changes
- Historical closed-candle data only
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from research.historical_context_sequence import (
    build_context_sequence_from_dataframe,
)
from research.historical_regime_transition_audit import (
    classify_research_regime,
)


def build_regime_timeline(
    df,
) -> list[dict[str, Any]]:
    """
    Convert historical BTC Klines into an ordered
    BULL / BEAR / RANGE timeline.
    """

    contexts = (
        build_context_sequence_from_dataframe(
            df
        )
    )

    timeline: list[
        dict[str, Any]
    ] = []

    for snapshot in contexts:
        regime = classify_research_regime(
            snapshot
        )

        timeline.append(
            {
                "candle_time_ms": int(
                    snapshot[
                        "candle_time_ms"
                    ]
                ),
                "regime": regime,
                "latest_close": float(
                    snapshot[
                        "latest_close"
                    ]
                ),
            }
        )

    return timeline


def regime_counts(
    timeline: list[dict[str, Any]],
) -> Counter:
    """
    Count BULL / BEAR / RANGE timeline entries.
    """

    return Counter(
        item["regime"]
        for item in timeline
    )
