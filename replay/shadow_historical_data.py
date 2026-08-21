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


def fetch_klines_range(
    symbol: str,
    start_time_ms: int,
    end_time_ms: int,
    interval: str = "15m",
    page_limit: int = 500,
) -> pd.DataFrame:
    """
    Fetch a complete historical Kline range by paging
    backward through BingX's per-request Kline limit.

    The returned DataFrame is:
    - bounded to [start_time_ms, end_time_ms)
    - sorted oldest -> newest
    - deduplicated by candle Time
    """

    if start_time_ms >= end_time_ms:
        raise ValueError(
            "start_time_ms must be before end_time_ms"
        )

    if page_limit < 1 or page_limit > 500:
        raise ValueError(
            "page_limit must be between 1 and 500"
        )

    all_klines: list[dict[str, Any]] = []

    current_end_ms = end_time_ms

    while current_end_ms > start_time_ms:

        klines = fetch_klines(
            symbol=symbol,
            interval=interval,
            limit=page_limit,
            start_time_ms=start_time_ms,
            end_time_ms=current_end_ms,
        )

        df = klines_to_shadow_dataframe(
            klines
        )

        if df.empty:
            break

        all_klines.extend(
            klines
        )

        oldest_ms = int(
            df.iloc[0]["Time"]
        )

        if oldest_ms <= start_time_ms:
            break

        next_end_ms = (
            oldest_ms - 1
        )

        if next_end_ms >= current_end_ms:
            raise RuntimeError(
                "Historical Kline pagination "
                "cursor did not move backward"
            )

        current_end_ms = next_end_ms

    combined = klines_to_shadow_dataframe(
        all_klines
    )

    if combined.empty:
        return combined

    combined = combined[
        (combined["Time"] >= start_time_ms)
        & (combined["Time"] < end_time_ms)
    ].copy()

    combined = (
        combined
        .sort_values(
            "Time",
            ascending=True,
        )
        .drop_duplicates(
            subset=["Time"]
        )
        .reset_index(drop=True)
    )

    return combined


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
