from __future__ import annotations

from collections import defaultdict
from typing import Any

import pandas as pd


FORWARD_HORIZONS = {
    "15m": 1,
    "45m": 3,
    "90m": 6,
    "3h": 12,
}


def calculate_forward_returns(
    timeline: list[dict[str, Any]],
    kline_df: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Calculate future BTC returns for each historical regime context.

    Future prices are used for evaluation only and are never fed back
    into the regime classifier.
    """
    if not timeline:
        return []

    df = kline_df.copy().sort_values("Time").reset_index(drop=True)

    price_by_time = {
        int(row["Time"]): float(row["Close"])
        for _, row in df.iterrows()
    }

    interval_ms = 15 * 60 * 1000
    records: list[dict[str, Any]] = []

    for item in timeline:
        candle_time_ms = int(item["candle_time_ms"])
        current_close = float(item["latest_close"])
        regime = str(item["regime"])

        record: dict[str, Any] = {
            "candle_time_ms": candle_time_ms,
            "regime": regime,
            "latest_close": current_close,
        }

        complete = True

        for label, bars_ahead in FORWARD_HORIZONS.items():
            future_time_ms = candle_time_ms + bars_ahead * interval_ms

            if future_time_ms not in price_by_time:
                complete = False
                break

            future_close = price_by_time[future_time_ms]
            forward_return = (future_close / current_close - 1.0) * 100.0

            record[f"return_{label}"] = forward_return

        if complete:
            records.append(record)

    return records


def summarize_forward_returns(
    records: list[dict[str, Any]],
) -> dict[str, dict[str, dict[str, float]]]:
    summary: dict[str, dict[str, dict[str, float]]] = {}

    grouped: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for record in records:
        regime = record["regime"]

        for label in FORWARD_HORIZONS:
            grouped[regime][label].append(
                float(record[f"return_{label}"])
            )

    for regime in ("BULL", "BEAR", "RANGE"):
        summary[regime] = {}

        for label in FORWARD_HORIZONS:
            values = grouped[regime][label]

            if not values:
                summary[regime][label] = {
                    "count": 0,
                    "average_return": 0.0,
                    "up_rate": 0.0,
                    "down_rate": 0.0,
                }
                continue

            count = len(values)
            up_count = sum(value > 0 for value in values)
            down_count = sum(value < 0 for value in values)

            summary[regime][label] = {
                "count": count,
                "average_return": sum(values) / count,
                "up_rate": up_count / count * 100.0,
                "down_rate": down_count / count * 100.0,
            }

    return summary
