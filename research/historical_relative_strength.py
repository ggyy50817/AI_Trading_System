"""
Historical Relative Strength V1

Compare historical Altcoin momentum against BTC momentum
using only fully closed candles available before a Shadow
trade timestamp.

Research only:
- No live trading
- No Strategy A modification
- No automatic parameter changes
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


INTERVAL = "15m"
INTERVAL_MS = 15 * 60 * 1000
KLINE_LIMIT = 100


def load_historical_close_sequence(
    symbol: str,
    timestamp: str | datetime,
    sequence_length: int = 20,
) -> list[dict[str, Any]]:
    """
    Return fully closed historical candles for a symbol,
    ordered oldest -> newest.
    """

    if sequence_length < 2:
        raise ValueError(
            "sequence_length must be >= 2"
        )

    snapshot_time_ms = timestamp_to_ms(
        timestamp
    )

    klines = fetch_klines(
        symbol=symbol,
        interval=INTERVAL,
        limit=KLINE_LIMIT,
        end_time_ms=snapshot_time_ms,
    )

    df = klines_to_shadow_dataframe(
        klines
    )

    if df.empty:
        raise ValueError(
            f"No historical klines for {symbol}"
        )

    # Strict anti-lookahead:
    # candle must be fully closed before snapshot time.
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

    if len(df) < sequence_length:
        raise ValueError(
            f"Insufficient historical candles "
            f"for {symbol}: {len(df)}"
        )

    df = df.tail(
        sequence_length
    )

    return [
        {
            "candle_time_ms": int(row["Time"]),
            "close": float(row["Close"]),
        }
        for _, row in df.iterrows()
    ]


def close_return(
    sequence: list[dict[str, Any]],
    candles: int,
) -> float:
    """
    Percentage return over N closed candles.
    Positive = price rose.
    Negative = price fell.
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
        sequence[-(candles + 1)]["close"]
    )

    end = float(
        sequence[-1]["close"]
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


def relative_strength(
    alt_return: float,
    btc_return: float,
) -> float:
    """
    Altcoin return minus BTC return.

    Positive = Altcoin outperformed BTC.
    Negative = Altcoin underperformed BTC.
    """

    return (
        float(alt_return)
        - float(btc_return)
    )


def relative_strength_direction(
    value: float,
) -> str:
    """
    Convert relative strength into a research label.
    """

    if value > 0:
        return "OUTPERFORM"

    if value < 0:
        return "UNDERPERFORM"

    return "FLAT"
