"""
Historical Context Snapshot V1

Reconstruct the BTC market context that was available
at a Shadow trade timestamp.

Research only:
- Historical analysis only
- No live orders
- No Strategy A modification
- No automatic parameter changes
- Strict anti-lookahead boundary
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
from ta.volatility import AverageTrueRange

from replay.shadow_historical_data import (
    fetch_klines,
    klines_to_shadow_dataframe,
    timestamp_to_ms,
)


BTC_SYMBOL = "BTC-USDT"
INTERVAL = "15m"
KLINE_LIMIT = 100


def build_indicators(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate the indicators required by Market Regime V1.
    """

    if df.empty:
        return df

    df = df.copy()

    df["MA20"] = (
        df["Close"]
        .rolling(window=20)
        .mean()
    )

    df["MA60"] = (
        df["Close"]
        .rolling(window=60)
        .mean()
    )

    atr = AverageTrueRange(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=14,
    )

    df["ATR"] = atr.average_true_range()

    df["VolumeMA20"] = (
        df["Volume"]
        .rolling(window=20)
        .mean()
    )

    df["VolumeRatio"] = (
        df["Volume"] / df["VolumeMA20"]
    )

    return df


def load_historical_snapshot(
    timestamp: str | datetime,
) -> dict[str, Any]:
    """
    Reconstruct BTC market context using only candles
    available at or before the supplied timestamp.
    """

    snapshot_time_ms = timestamp_to_ms(timestamp)

    klines = fetch_klines(
        symbol=BTC_SYMBOL,
        interval=INTERVAL,
        limit=KLINE_LIMIT,
        end_time_ms=snapshot_time_ms,
    )

    df = klines_to_shadow_dataframe(klines)

    if df.empty:
        raise ValueError(
            "No historical BTC klines available"
        )

    # Strict anti-lookahead boundary.
    #
    # Time is the candle OPEN time. A 15m candle that opened
    # before the Shadow timestamp may still have been forming
    # when the decision was made. Only candles that were fully
    # closed by the snapshot timestamp are allowed.
    interval_ms = 15 * 60 * 1000

    df = df[
        (df["Time"] + interval_ms)
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

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    latest_close = float(
        latest["Close"]
    )

    latest_ma20 = float(
        latest["MA20"]
    )

    latest_ma60 = float(
        latest["MA60"]
    )

    latest_atr = float(
        latest["ATR"]
    )

    latest_volume = float(
        latest["Volume"]
    )

    latest_volume_ma20 = float(
        latest["VolumeMA20"]
    )

    volume_ratio = float(
        latest["VolumeRatio"]
    )

    ma20_previous = float(
        previous["MA20"]
    )

    ma20_slope = (
        latest_ma20 - ma20_previous
    )

    atr_pct = (
        latest_atr / latest_close
        if latest_close > 0
        else 0.0
    )

    return {
        "timestamp": (
            timestamp.isoformat()
            if isinstance(timestamp, datetime)
            else timestamp
        ),
        "symbol": BTC_SYMBOL,
        "interval": INTERVAL,
        "candle_count": len(df),
        "latest_candle_time_ms": int(
            latest["Time"]
        ),
        "snapshot_time_ms": snapshot_time_ms,
        "latest_close": latest_close,
        "ma20": latest_ma20,
        "ma60": latest_ma60,
        "ma20_slope": ma20_slope,
        "atr": latest_atr,
        "atr_pct": atr_pct,
        "volume": latest_volume,
        "volume_ma20": latest_volume_ma20,
        "volume_ratio": volume_ratio,
    }
