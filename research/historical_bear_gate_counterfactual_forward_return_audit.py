"""
Historical BEAR Gate Counterfactual Forward Return Audit V1

Purpose:
- Compare forward BTC returns from the first available BEAR signal
  at different gate stages:
    RAW
    RAW+ATR+VOLUME
    PRODUCTION (+ Slope)
- Run both:
    1. All available episodes
    2. Matched Production-available episodes

The matched comparison is important because all-available groups have
different episode counts and therefore are not a clean like-for-like
comparison.

Research only:
- No Strategy A modification
- No production threshold modification
- No automatic parameter changes
"""

from __future__ import annotations

from datetime import datetime, timezone
from collections import defaultdict

import numpy as np

from replay.shadow_historical_data import fetch_klines_range
from research.historical_context_sequence import (
    build_context_sequence_from_dataframe,
)
from research.historical_regime_forward_return_audit import (
    FORWARD_HORIZONS,
)
from research.historical_bear_gate_lag_attribution_audit import (
    group_raw_bear_episodes,
    find_first_path_context,
)


START = datetime(2026, 6, 1, tzinfo=timezone.utc)
END = datetime(2026, 8, 21, tzinfo=timezone.utc)

INTERVAL_MS = 15 * 60 * 1000

PATH_NAMES = (
    "RAW",
    "RAW+ATR+VOLUME",
    "PRODUCTION",
)


def build_close_map(df):
    return {
        int(row["Time"]): float(row["Close"])
        for _, row in df.iterrows()
    }


def calculate_forward_returns(
    context,
    close_map,
):
    candle_time_ms = int(
        context["candle_time_ms"]
    )

    current_close = float(
        context["latest_close"]
    )

    returns = {}

    for label, bars_ahead in FORWARD_HORIZONS.items():
        future_time_ms = (
            candle_time_ms
            + int(bars_ahead) * INTERVAL_MS
        )

        if future_time_ms not in close_map:
            return None

        future_close = float(
            close_map[future_time_ms]
        )

        returns[label] = (
            future_close / current_close
            - 1.0
        ) * 100.0

    return returns


def summarize(values):
    if not values:
        return None

    array = np.asarray(
        values,
        dtype=float,
    )

    positive = int(
        np.sum(array > 0)
    )

    negative = int(
        np.sum(array < 0)
    )

    zero = int(
        np.sum(array == 0)
    )

    count = len(array)

    return {
        "n": count,
        "average": float(
            np.mean(array)
        ),
        "median": float(
            np.percentile(array, 50)
        ),
        "p25": float(
            np.percentile(array, 25)
        ),
        "p75": float(
            np.percentile(array, 75)
        ),
        "minimum": float(
            np.min(array)
        ),
        "maximum": float(
            np.max(array)
        ),
        "positive": positive,
        "negative": negative,
        "zero": zero,
        "positive_rate": (
            positive / count * 100.0
        ),
        "negative_rate": (
            negative / count * 100.0
        ),
    }


def build_episode_records(
    episodes,
    close_map,
):
    records = []

    for episode_index, episode in enumerate(
        episodes,
        start=1,
    ):
        raw_start_ms = int(
            episode[0]["candle_time_ms"]
        )

        record = {
            "episode_index": episode_index,
            "raw_start_ms": raw_start_ms,
            "episode_bars": len(episode),
            "paths": {},
        }

        for path_name in PATH_NAMES:
            context = find_first_path_context(
                episode,
                path_name,
            )

            if context is None:
                record["paths"][path_name] = None
                continue

            forward_returns = (
                calculate_forward_returns(
                    context,
                    close_map,
                )
            )

            if forward_returns is None:
                record["paths"][path_name] = None
                continue

            signal_ms = int(
                context["candle_time_ms"]
            )

            lag_bars = (
                signal_ms - raw_start_ms
            ) // INTERVAL_MS

            record["paths"][path_name] = {
                "signal_ms": signal_ms,
                "lag_bars": int(lag_bars),
                "returns": forward_returns,
            }

        records.append(record)

    return records


def collect_path_values(
    records,
    path_name,
):
    grouped = defaultdict(list)

    for record in records:
        path = record["paths"].get(
            path_name
        )

        if path is None:
            continue

        for label in FORWARD_HORIZONS:
            grouped[label].append(
                float(
                    path["returns"][label]
                )
            )

    return grouped


def print_path_summary(
    path_name,
    records,
):
    grouped = collect_path_values(
        records,
        path_name,
    )

    available_n = sum(
        1
        for record in records
        if record["paths"].get(
            path_name
        ) is not None
    )

    print()
    print(f"--- {path_name} ---")
    print(
        f"AVAILABLE EPISODES           : "
        f"{available_n}"
    )

    for label in FORWARD_HORIZONS:
        stats = summarize(
            grouped[label]
        )

        if stats is None:
            print(
                f"{label:5s}                        : "
                f"NO DATA"
            )
            continue

        print(
            f"{label:5s}  "
            f"N={stats['n']:3d}  "
            f"AVG={stats['average']:+.6f}%  "
            f"MED={stats['median']:+.6f}%  "
            f"UP={stats['positive_rate']:6.2f}%  "
            f"DOWN={stats['negative_rate']:6.2f}%"
        )


def print_three_hour_comparison(
    title,
    records,
):
    print()
    print("=" * 110)
    print(title)
    print("=" * 110)

    for path_name in PATH_NAMES:
        values = []

        for record in records:
            path = record["paths"].get(
                path_name
            )

            if path is None:
                continue

            values.append(
                float(
                    path["returns"]["3h"]
                )
            )

        stats = summarize(values)

        if stats is None:
            print(
                f"{path_name:28s}: NO DATA"
            )
            continue

        print(
            f"{path_name:28s}: "
            f"N={stats['n']:3d}  "
            f"AVG={stats['average']:+.6f}%  "
            f"MED={stats['median']:+.6f}%  "
            f"UP={stats['positive_rate']:6.2f}%  "
            f"DOWN={stats['negative_rate']:6.2f}%"
        )


def run_audit():
    start_ms = int(
        START.timestamp() * 1000
    )

    end_ms = int(
        END.timestamp() * 1000
    )

    print("=" * 110)
    print(
        "HISTORICAL BEAR GATE COUNTERFACTUAL "
        "FORWARD RETURN AUDIT V1"
    )
    print("=" * 110)

    df = fetch_klines_range(
        "BTC-USDT",
        start_ms,
        end_ms,
        interval="15m",
        page_limit=500,
    )

    contexts = (
        build_context_sequence_from_dataframe(
            df
        )
    )

    episodes = group_raw_bear_episodes(
        contexts
    )

    close_map = build_close_map(df)

    records = build_episode_records(
        episodes,
        close_map,
    )

    complete_raw_records = [
        record
        for record in records
        if record["paths"]["RAW"]
        is not None
    ]

    matched_records = [
        record
        for record in records
        if all(
            record["paths"][path_name]
            is not None
            for path_name in PATH_NAMES
        )
    ]

    print()
    print("KLINES                       :", len(df))
    print("MATURE CONTEXTS              :", len(contexts))
    print("RAW BEAR EPISODES            :", len(episodes))
    print(
        "COMPLETE RAW RECORDS         :",
        len(complete_raw_records),
    )
    print(
        "MATCHED PRODUCTION EPISODES  :",
        len(matched_records),
    )

    print()
    print("=" * 110)
    print("1. ALL AVAILABLE EPISODES")
    print("=" * 110)

    for path_name in PATH_NAMES:
        print_path_summary(
            path_name,
            records,
        )

    print_three_hour_comparison(
        "2. ALL-AVAILABLE 3H COMPARISON",
        records,
    )

    print()
    print("=" * 110)
    print("3. MATCHED PRODUCTION-AVAILABLE EPISODES")
    print("=" * 110)

    print(
        "These are the same Raw BEAR episodes "
        "that eventually reached Production."
    )
    print(
        "This is the primary like-for-like "
        "counterfactual comparison."
    )

    for path_name in PATH_NAMES:
        print_path_summary(
            path_name,
            matched_records,
        )

    print_three_hour_comparison(
        "4. MATCHED 3H COMPARISON",
        matched_records,
    )

    print()
    print("=" * 110)
    print("5. MATCHED EPISODE DETAILS — 3H")
    print("=" * 110)

    for index, record in enumerate(
        matched_records,
        start=1,
    ):
        raw = record["paths"]["RAW"]
        volume = record[
            "paths"
        ]["RAW+ATR+VOLUME"]
        production = record[
            "paths"
        ]["PRODUCTION"]

        raw_dt = datetime.fromtimestamp(
            record["raw_start_ms"] / 1000,
            tz=timezone.utc,
        )

        print(
            f"{index:03d}  "
            f"{raw_dt.isoformat()}  "
            f"EP_BARS={record['episode_bars']:3d}  "
            f"VOL_LAG={volume['lag_bars']:2d}  "
            f"PROD_LAG={production['lag_bars']:2d}  "
            f"RAW3H={raw['returns']['3h']:+.6f}%  "
            f"VOL3H={volume['returns']['3h']:+.6f}%  "
            f"PROD3H={production['returns']['3h']:+.6f}%"
        )

    print()
    print("=" * 110)
    print("6. DIRECTIONAL TRANSITION — MATCHED 3H")
    print("=" * 110)

    raw_down_prod_up = 0
    raw_down_prod_down = 0
    raw_up_prod_up = 0
    raw_up_prod_down = 0

    for record in matched_records:
        raw_return = float(
            record["paths"]["RAW"][
                "returns"
            ]["3h"]
        )

        production_return = float(
            record["paths"]["PRODUCTION"][
                "returns"
            ]["3h"]
        )

        if (
            raw_return < 0
            and production_return > 0
        ):
            raw_down_prod_up += 1

        elif (
            raw_return < 0
            and production_return < 0
        ):
            raw_down_prod_down += 1

        elif (
            raw_return > 0
            and production_return > 0
        ):
            raw_up_prod_up += 1

        elif (
            raw_return > 0
            and production_return < 0
        ):
            raw_up_prod_down += 1

    matched_n = len(
        matched_records
    )

    def pct(value):
        if matched_n == 0:
            return 0.0

        return (
            value / matched_n * 100.0
        )

    print(
        f"RAW DOWN -> PROD UP          : "
        f"{raw_down_prod_up} "
        f"({pct(raw_down_prod_up):.2f}%)"
    )
    print(
        f"RAW DOWN -> PROD DOWN        : "
        f"{raw_down_prod_down} "
        f"({pct(raw_down_prod_down):.2f}%)"
    )
    print(
        f"RAW UP -> PROD UP            : "
        f"{raw_up_prod_up} "
        f"({pct(raw_up_prod_up):.2f}%)"
    )
    print(
        f"RAW UP -> PROD DOWN          : "
        f"{raw_up_prod_down} "
        f"({pct(raw_up_prod_down):.2f}%)"
    )

    print()
    print("=" * 110)
    print("7. FINAL CHECK")
    print("=" * 110)

    raw_episode_check = (
        len(episodes) == 276
    )

    matched_check = (
        len(matched_records) == 21
    )

    matched_complete_check = all(
        all(
            record["paths"][path_name]
            is not None
            for path_name in PATH_NAMES
        )
        for record in matched_records
    )

    production_available_count = sum(
        1
        for record in records
        if record["paths"]["PRODUCTION"]
        is not None
    )

    production_check = (
        production_available_count
        == 21
    )

    directional_total = (
        raw_down_prod_up
        + raw_down_prod_down
        + raw_up_prod_up
        + raw_up_prod_down
    )

    directional_check = (
        directional_total
        == matched_n
    )

    print(
        "RAW EPISODE CHECK            :",
        "PASS"
        if raw_episode_check
        else "FAIL",
    )
    print(
        "MATCHED EPISODE CHECK        :",
        "PASS"
        if matched_check
        else "FAIL",
    )
    print(
        "MATCHED COMPLETE CHECK       :",
        "PASS"
        if matched_complete_check
        else "FAIL",
    )
    print(
        "PRODUCTION AVAILABILITY CHECK:",
        "PASS"
        if production_check
        else "FAIL",
    )
    print(
        "DIRECTION CONSERVATION CHECK :",
        "PASS"
        if directional_check
        else "FAIL",
    )

    overall_check = (
        raw_episode_check
        and matched_check
        and matched_complete_check
        and production_check
        and directional_check
    )

    print(
        "OVERALL CHECK                :",
        "PASS"
        if overall_check
        else "FAIL",
    )

    print("=" * 110)


if __name__ == "__main__":
    run_audit()
