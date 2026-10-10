"""
Shadow Data Quality Gate V1.

Research only. No exchange orders.
Does not modify original Shadow records.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from math import isfinite


INTERVAL_MS = 15 * 60 * 1000


def validate_shadow_entry_price(
    record: dict,
    historical_klines,
) -> dict:
    """
    Validate Shadow entry against its signal-containing 15m candle.

    historical_klines must contain:
    Time, Low, High

    Time is the candle opening timestamp in milliseconds.
    """

    result = {
        "symbol": record.get("symbol"),
        "timestamp": record.get("timestamp"),
        "status": "REJECT",
        "reason": None,
        "entry_price": record.get("entry_price"),
        "candle_time": None,
    }

    try:
        entry = float(record["entry_price"])
        if not isfinite(entry) or entry <= 0:
            raise ValueError
    except (KeyError, TypeError, ValueError):
        result["reason"] = "INVALID_ENTRY_PRICE"
        return result

    timestamp = record.get("timestamp")

    try:
        dt = (
            timestamp
            if isinstance(timestamp, datetime)
            else datetime.fromisoformat(timestamp)
        )

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone(timedelta(hours=8))
            )

        signal_ms = int(dt.timestamp() * 1000)

    except (TypeError, ValueError):
        result["reason"] = "INVALID_TIMESTAMP"
        return result

    if historical_klines is None or historical_klines.empty:
        result["reason"] = "MISSING_KLINES"
        return result

    candle_open_ms = (
        signal_ms // INTERVAL_MS
    ) * INTERVAL_MS

    matching = historical_klines[
        historical_klines["Time"] == candle_open_ms
    ]

    if matching.empty:
        result["reason"] = "SIGNAL_CANDLE_NOT_FOUND"
        return result

    candle = matching.iloc[0]

    try:
        low = float(candle["Low"])
        high = float(candle["High"])
    except (TypeError, ValueError):
        result["reason"] = "INVALID_CANDLE"
        return result

    if not (
        isfinite(low)
        and isfinite(high)
        and low > 0
        and high >= low
    ):
        result["reason"] = "INVALID_CANDLE"
        return result

    result["candle_time"] = candle_open_ms
    result["candle_low"] = low
    result["candle_high"] = high

    if low <= entry <= high:
        result["status"] = "PASS"
        result["reason"] = "PRICE_MATCH"
    else:
        result["reason"] = "PRICE_MISMATCH"

    return result
