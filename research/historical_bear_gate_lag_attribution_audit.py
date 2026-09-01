"""
Historical BEAR Gate Lag Attribution Audit V1

Purpose:
- Attribute PASSED BEAR scarcity and confirmation lag across:
    RAW MA STRUCTURE
    + ATR gate
    + Volume gate
    + Slope gate
- Measure how much later Production BEAR becomes available
  relative to the start of each raw BEAR episode.

Important:
- Counterfactual research only.
- "Lag" does not imply causality by itself.
- No Strategy A modification.
- No production threshold modification.
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from replay.shadow_historical_data import fetch_klines_range
from research.historical_context_sequence import (
    build_context_sequence_from_dataframe,
)
from research.historical_regime_gate_distribution_audit import (
    ATR_THRESHOLD,
    VOLUME_THRESHOLD,
    SLOPE_THRESHOLD,
    classify_raw_structure,
)


START = datetime(2026, 6, 1, tzinfo=timezone.utc)
END = datetime(2026, 8, 21, tzinfo=timezone.utc)

INTERVAL_MS = 15 * 60 * 1000


def gate_flags(context):
    close = float(context["latest_close"])
    atr_pct = float(context["atr_pct"])
    volume_ratio = float(context["volume_ratio"])
    slope = float(context["ma20_slope"])

    return {
        "atr_pass": (
            atr_pct <= ATR_THRESHOLD
        ),
        "volume_pass": (
            volume_ratio >= VOLUME_THRESHOLD
        ),
        "slope_pass": (
            abs(slope)
            >= close * SLOPE_THRESHOLD
        ),
    }


def classify_bear_paths(context):
    raw_bear = (
        classify_raw_structure(context)
        == "BEAR"
    )

    flags = gate_flags(context)

    raw = raw_bear

    raw_atr = (
        raw
        and flags["atr_pass"]
    )

    raw_atr_volume = (
        raw_atr
        and flags["volume_pass"]
    )

    production = (
        raw_atr_volume
        and flags["slope_pass"]
    )

    return {
        "RAW": raw,
        "RAW+ATR": raw_atr,
        "RAW+ATR+VOLUME": raw_atr_volume,
        "PRODUCTION": production,
    }


def group_raw_bear_episodes(contexts):
    raw_bear_contexts = [
        context
        for context in contexts
        if classify_raw_structure(context) == "BEAR"
    ]

    raw_bear_contexts = sorted(
        raw_bear_contexts,
        key=lambda item: int(
            item["candle_time_ms"]
        ),
    )

    episodes = []

    current = []

    for context in raw_bear_contexts:
        timestamp_ms = int(
            context["candle_time_ms"]
        )

        if not current:
            current = [context]
            continue

        previous_ms = int(
            current[-1]["candle_time_ms"]
        )

        if (
            timestamp_ms - previous_ms
            == INTERVAL_MS
        ):
            current.append(context)
        else:
            episodes.append(current)
            current = [context]

    if current:
        episodes.append(current)

    return episodes


def summarize(values):
    if not values:
        return None

    array = np.asarray(
        values,
        dtype=float,
    )

    return {
        "n": len(values),
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
    }


def find_first_path_context(
    episode,
    path_name,
):
    for context in episode:
        paths = classify_bear_paths(
            context
        )

        if paths[path_name]:
            return context

    return None


def run_audit():
    start_ms = int(
        START.timestamp() * 1000
    )

    end_ms = int(
        END.timestamp() * 1000
    )

    print("=" * 110)
    print("HISTORICAL BEAR GATE LAG ATTRIBUTION AUDIT V1")
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

    path_names = (
        "RAW",
        "RAW+ATR",
        "RAW+ATR+VOLUME",
        "PRODUCTION",
    )

    path_counts = {
        name: 0
        for name in path_names
    }

    raw_bear_count = 0

    for context in contexts:
        paths = classify_bear_paths(
            context
        )

        if paths["RAW"]:
            raw_bear_count += 1

        for name in path_names:
            if paths[name]:
                path_counts[name] += 1

    episodes = group_raw_bear_episodes(
        contexts
    )

    episode_records = []

    for episode in episodes:
        raw_start = episode[0]

        raw_start_ms = int(
            raw_start["candle_time_ms"]
        )

        raw_start_close = float(
            raw_start["latest_close"]
        )

        record = {
            "raw_start_ms": raw_start_ms,
            "raw_start_close": raw_start_close,
            "episode_bars": len(episode),
            "paths": {},
        }

        for path_name in path_names:
            first_context = (
                find_first_path_context(
                    episode,
                    path_name,
                )
            )

            if first_context is None:
                record["paths"][
                    path_name
                ] = None
                continue

            first_ms = int(
                first_context[
                    "candle_time_ms"
                ]
            )

            first_close = float(
                first_context[
                    "latest_close"
                ]
            )

            lag_bars = (
                first_ms - raw_start_ms
            ) // INTERVAL_MS

            price_move = (
                first_close
                / raw_start_close
                - 1.0
            ) * 100.0

            record["paths"][
                path_name
            ] = {
                "first_ms": first_ms,
                "lag_bars": int(
                    lag_bars
                ),
                "lag_minutes": int(
                    lag_bars * 15
                ),
                "price_move_pct": float(
                    price_move
                ),
            }

        episode_records.append(
            record
        )

    print()
    print("KLINES                       :", len(df))
    print("MATURE CONTEXTS              :", len(contexts))
    print("RAW BEAR CONTEXTS            :", raw_bear_count)
    print("RAW BEAR EPISODES            :", len(episodes))

    print()
    print("=" * 110)
    print("1. COUNTERFACTUAL PATH COUNTS")
    print("=" * 110)

    previous_count = None

    for name in path_names:
        count = path_counts[name]

        pct_of_raw = (
            count / raw_bear_count * 100.0
            if raw_bear_count
            else 0.0
        )

        if previous_count is None:
            removed = 0
        else:
            removed = (
                previous_count - count
            )

        print()
        print(
            f"{name:28s}: "
            f"{count}"
        )
        print(
            f"{'  % OF RAW':28s}: "
            f"{pct_of_raw:.2f}%"
        )

        if previous_count is not None:
            print(
                f"{'  REMOVED BY NEW LAYER':28s}: "
                f"{removed}"
            )

        previous_count = count

    print()
    print("=" * 110)
    print("2. EPISODE AVAILABILITY")
    print("=" * 110)

    availability = {}

    for name in path_names:
        available_records = [
            record
            for record in episode_records
            if record["paths"][name]
            is not None
        ]

        availability[name] = len(
            available_records
        )

        pct = (
            len(available_records)
            / len(episode_records)
            * 100.0
            if episode_records
            else 0.0
        )

        print(
            f"{name:28s}: "
            f"{len(available_records):4d} "
            f"({pct:6.2f}%)"
        )

    print()
    print("=" * 110)
    print("3. FIRST-AVAILABLE LAG FROM RAW BEAR EPISODE START")
    print("=" * 110)

    for name in path_names:
        lag_bars_values = []
        price_move_values = []

        for record in episode_records:
            path = record["paths"][name]

            if path is None:
                continue

            lag_bars_values.append(
                path["lag_bars"]
            )

            price_move_values.append(
                path["price_move_pct"]
            )

        lag_stats = summarize(
            lag_bars_values
        )

        move_stats = summarize(
            price_move_values
        )

        print()
        print(f"--- {name} ---")

        if lag_stats is None:
            print("NO AVAILABLE EPISODES")
            continue

        print(
            f"N                            : "
            f"{lag_stats['n']}"
        )
        print(
            f"LAG BARS AVG                 : "
            f"{lag_stats['average']:.3f}"
        )
        print(
            f"LAG BARS MEDIAN              : "
            f"{lag_stats['median']:.3f}"
        )
        print(
            f"LAG BARS P25                 : "
            f"{lag_stats['p25']:.3f}"
        )
        print(
            f"LAG BARS P75                 : "
            f"{lag_stats['p75']:.3f}"
        )
        print(
            f"LAG BARS MIN                 : "
            f"{lag_stats['minimum']:.0f}"
        )
        print(
            f"LAG BARS MAX                 : "
            f"{lag_stats['maximum']:.0f}"
        )

        print(
            f"LAG MINUTES AVG              : "
            f"{lag_stats['average'] * 15:.2f}"
        )
        print(
            f"LAG MINUTES MEDIAN           : "
            f"{lag_stats['median'] * 15:.2f}"
        )

        print(
            f"PRICE MOVE AVG               : "
            f"{move_stats['average']:+.6f}%"
        )
        print(
            f"PRICE MOVE MEDIAN            : "
            f"{move_stats['median']:+.6f}%"
        )
        print(
            f"PRICE MOVE P25               : "
            f"{move_stats['p25']:+.6f}%"
        )
        print(
            f"PRICE MOVE P75               : "
            f"{move_stats['p75']:+.6f}%"
        )

    print()
    print("=" * 110)
    print("4. PRODUCTION-AVAILABLE EPISODE DETAILS")
    print("=" * 110)

    production_episode_count = 0

    for record in episode_records:
        production = record[
            "paths"
        ]["PRODUCTION"]

        if production is None:
            continue

        production_episode_count += 1

        raw_dt = datetime.fromtimestamp(
            record["raw_start_ms"] / 1000,
            tz=timezone.utc,
        )

        atr_path = record[
            "paths"
        ]["RAW+ATR"]

        volume_path = record[
            "paths"
        ]["RAW+ATR+VOLUME"]

        print(
            f"{production_episode_count:03d}  "
            f"{raw_dt.isoformat()}  "
            f"EP_BARS={record['episode_bars']:3d}  "
            f"ATR_LAG={atr_path['lag_bars'] if atr_path else 'NA'}  "
            f"VOL_LAG={volume_path['lag_bars'] if volume_path else 'NA'}  "
            f"PROD_LAG={production['lag_bars']}  "
            f"PROD_MOVE={production['price_move_pct']:+.6f}%"
        )

    print()
    print("=" * 110)
    print("5. FINAL CHECK")
    print("=" * 110)

    raw_count_check = (
        raw_bear_count
        == path_counts["RAW"]
    )

    monotonic_check = (
        path_counts["RAW"]
        >= path_counts["RAW+ATR"]
        >= path_counts["RAW+ATR+VOLUME"]
        >= path_counts["PRODUCTION"]
    )

    episode_monotonic_check = (
        availability["RAW"]
        >= availability["RAW+ATR"]
        >= availability[
            "RAW+ATR+VOLUME"
        ]
        >= availability["PRODUCTION"]
    )

    production_context_check = (
        path_counts["PRODUCTION"]
        == 108
    )

    print(
        "RAW COUNT CHECK              :",
        "PASS" if raw_count_check else "FAIL",
    )
    print(
        "PATH MONOTONIC CHECK         :",
        "PASS" if monotonic_check else "FAIL",
    )
    print(
        "EPISODE MONOTONIC CHECK      :",
        "PASS"
        if episode_monotonic_check
        else "FAIL",
    )
    print(
        "PRODUCTION CONTEXT CHECK      :",
        "PASS"
        if production_context_check
        else "FAIL",
    )

    overall_check = (
        raw_count_check
        and monotonic_check
        and episode_monotonic_check
        and production_context_check
    )

    print(
        "OVERALL CHECK                :",
        "PASS" if overall_check else "FAIL",
    )

    print("=" * 110)


if __name__ == "__main__":
    run_audit()
