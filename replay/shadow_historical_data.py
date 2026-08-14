"""
Shadow Historical Data V1

Historical Kline data layer for Shadow Replay.

This module is isolated from live scanner trading logic.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import requests

from scanner.bingx_api import BASE_URL


KLINE_ENDPOINT = "/openApi/swap/v3/quote/klines"


def timestamp_to_ms(timestamp: str | datetime) -> int:
    if isinstance(timestamp, datetime):
        dt = timestamp
    else:
        dt = datetime.fromisoformat(timestamp)

    return int(dt.timestamp() * 1000)


def fetch_klines(
    symbol: str,
    interval: str = "15m",
    limit: int = 500,
    start_time_ms: int | None = None,
    end_time_ms: int | None = None,
) -> list[dict[str, Any]]:

    url = f"{BASE_URL}{KLINE_ENDPOINT}"

    params: dict[str, Any] = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
    }

    if start_time_ms is not None:
        params["startTime"] = start_time_ms

    if end_time_ms is not None:
        params["endTime"] = end_time_ms

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()

    payload = response.json()

    if payload.get("code") != 0:
        raise RuntimeError(
            f"BingX Kline error: {payload}"
        )

    return payload.get("data", [])


def klines_to_shadow_dataframe(
    klines: list[dict[str, Any]],
) -> pd.DataFrame:

    df = pd.DataFrame(klines)

    if df.empty:
        return df

    df = df.rename(
        columns={
            "time": "Time",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )

    numeric_columns = [
        "Time",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(
        subset=["Time", "Open", "High", "Low", "Close"]
    )

    df["Time"] = df["Time"].astype("int64")

    # BingX returns newest -> oldest.
    # Replay must always run oldest -> newest.
    df = (
        df.sort_values("Time", ascending=True)
        .drop_duplicates(subset=["Time"])
        .reset_index(drop=True)
    )

    return df


def load_shadow_future_klines(
    shadow_record: dict,
    interval: str = "15m",
    limit: int = 500,
) -> pd.DataFrame:

    timestamp = shadow_record.get("timestamp")

    if not timestamp:
        raise ValueError("Shadow record missing timestamp")

    symbol = shadow_record.get("symbol")

    if not symbol:
        raise ValueError("Shadow record missing symbol")

    shadow_time_ms = timestamp_to_ms(timestamp)

    klines = fetch_klines(
        symbol=symbol,
        interval=interval,
        limit=limit,
        start_time_ms=shadow_time_ms,
    )

    df = klines_to_shadow_dataframe(klines)

    if df.empty:
        return df

    # Hard anti-lookahead boundary.
    df = df[df["Time"] > shadow_time_ms].copy()

    df = (
        df.sort_values("Time", ascending=True)
        .reset_index(drop=True)
    )

    return df
