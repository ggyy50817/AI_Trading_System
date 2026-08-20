"""
Historical Context Sequence V1

Reconstruct a sequence of historical BTC market contexts
available before a Shadow trade timestamp.

Research only:
- No live trading
- No Strategy A modification
- No automatic parameter changes
- Historical closed-candle data only
- Strict anti-lookahead boundary
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from replay.shadow_historical_data import (
    fetch_klines,
    klines_to_shadow_dataframe,
    timestamp_to_ms,
)
from research.historical_context_snapshot import (
    BTC_SYMBOL,
    INTERVAL,
    build_indicators,
)


INTERVAL_MS = 15 * 60 * 1000
KLINE_LIMIT = 100


def load_historical_context_sequence(
    timestamp: str | datetime,
    sequence_length: int = 20,
) -> list[dict[str, Any]]:
    """
    Return the most recent fully closed BTC contexts
    available at the supplied timestamp.

    The sequence is ordered oldest -> newest.
    """

    if sequence_length < 1:
        raise ValueError(
            "sequence_length must be >= 1"
        )

    snapshot_time_ms = timestamp_to_ms(
        timestamp
    )

    klines = fetch_klines(
        symbol=BTC_SYMBOL,
        interval=INTERVAL,
        limit=KLINE_LIMIT,
        end_time_ms=snapshot_time_ms,
    )

    df = klines_to_shadow_dataframe(
        klines
    )

    if df.empty:
        raise ValueError(
            "No historical BTC klines available"
        )

    # Strict anti-lookahead:
    # only candles fully closed by snapshot time.
    df = df[
        (df["Time"] + INTERVAL_MS)
        <= snapshot_time_ms
    ].copy()

    df = (
        df.sort_values(
            "Time",
            ascending=True,
        )
        .reset_index(drop=True)
    )

    if len(df) < 60:
        raise ValueError(
            f"Insufficient historical candles: {len(df)}"
        )

    df = build_indicators(df)

    start_index = max(
        1,
        len(df) - sequence_length,
    )

    sequence: list[
        dict[str, Any]
    ] = []

    for index in range(
        start_index,
        len(df),
    ):
        current = df.iloc[index]
        previous = df.iloc[index - 1]

        latest_close = float(
            current["Close"]
        )

        ma20 = float(
            current["MA20"]
        )

        ma60 = float(
            current["MA60"]
        )

        atr = float(
            current["ATR"]
        )

        volume = float(
            current["Volume"]
        )

        volume_ma20 = float(
            current["VolumeMA20"]
        )

        volume_ratio = float(
            current["VolumeRatio"]
        )

        ma20_previous = float(
            previous["MA20"]
        )

        ma20_slope = (
            ma20 - ma20_previous
        )

        atr_pct = (
            atr / latest_close
            if latest_close > 0
            else 0.0
        )

        sequence.append(
            {
                "candle_time_ms": int(
                    current["Time"]
                ),
                "latest_close": latest_close,
                "ma20": ma20,
                "ma60": ma60,
                "ma20_slope": ma20_slope,
                "atr": atr,
                "atr_pct": atr_pct,
                "volume": volume,
                "volume_ma20": volume_ma20,
                "volume_ratio": volume_ratio,
            }
        )

    return sequence
