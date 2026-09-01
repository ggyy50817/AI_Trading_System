"""
Historical BEAR Gate Episode Distribution Audit V1

Purpose:
- Analyze the distribution of 3h forward returns from independent
  PASSED BEAR episode starts.
- Determine whether positive average return is broad-based or
  dominated by a small number of extreme rebounds.

Research only:
- No live trading
- No Strategy A modification
- No automatic threshold changes
"""

from __future__ import annotations

from datetime import datetime, timezone
import numpy as np

from replay.shadow_historical_data import fetch_klines_range
from research.historical_context_sequence import (
    build_context_sequence_from_dataframe,
)
from research.historical_bear_gate_episode_audit import (
    build_close_map,
    collect_passed_bear_contexts,
    group_passed_bear_episodes,
    calculate_episode_forward_returns,
)


START = datetime(2026, 6, 1, tzinfo=timezone.utc)
END = datetime(2026, 8, 21, tzinfo=timezone.utc)


def percentile(values, q):
    return float(
        np.percentile(
            np.asarray(values, dtype=float),
            q,
        )
    )


def run_audit():
    start_ms = int(START.timestamp() * 1000)
    end_ms = int(END.timestamp() * 1000)

    print("=" * 110)
    print("HISTORICAL BEAR GATE EPISODE DISTRIBUTION AUDIT V1")
    print("=" * 110)

    df = fetch_klines_range(
        "BTC-USDT",
        start_ms,
        end_ms,
        interval="15m",
        page_limit=500,
    )

    contexts = build_context_sequence_from_dataframe(df)

    passed_bear = collect_passed_bear_contexts(
        contexts
    )

    episodes = group_passed_bear_episodes(
        passed_bear
    )

    close_map = build_close_map(df)

    records = []

    for episode in episodes:
        returns = calculate_episode_forward_returns(
            episode,
            close_map,
        )

        return_3h = returns.get("3h")

        if return_3h is None:
            continue

        start_time_ms = int(
            episode[0]["candle_time_ms"]
        )

        start_dt = datetime.fromtimestamp(
            start_time_ms / 1000,
            tz=timezone.utc,
        )

        records.append(
            {
                "start_time_ms": start_time_ms,
                "start_dt": start_dt,
                "bars": len(episode),
                "return_3h": float(return_3h),
            }
        )

    values = [
        record["return_3h"]
        for record in records
    ]

    print()
    print("KLINES                  :", len(df))
    print("MATURE CONTEXTS         :", len(contexts))
    print("PASSED BEAR CONTEXTS    :", len(passed_bear))
    print("BEAR PASSED EPISODES    :", len(episodes))
    print("COMPLETE 3H EPISODES    :", len(records))

    print()
    print("=" * 110)
    print("3H RETURN DISTRIBUTION")
    print("=" * 110)

    if not values:
        print("NO COMPLETE 3H RETURNS")
        return

    average = sum(values) / len(values)
    med = percentile(values, 50)

    p25 = percentile(values, 25)
    p75 = percentile(values, 75)

    minimum = min(values)
    maximum = max(values)

    positive = sum(value > 0 for value in values)
    negative = sum(value < 0 for value in values)
    zero = sum(value == 0 for value in values)

    print(f"COUNT                   : {len(values)}")
    print(f"AVERAGE                 : {average:+.6f}%")
    print(f"MEDIAN                  : {med:+.6f}%")
    print(f"P25                     : {p25:+.6f}%")
    print(f"P75                     : {p75:+.6f}%")
    print(f"MIN                     : {minimum:+.6f}%")
    print(f"MAX                     : {maximum:+.6f}%")

    print()
    print(f"POSITIVE                : {positive}")
    print(f"NEGATIVE                : {negative}")
    print(f"ZERO                    : {zero}")
    print(
        f"POSITIVE RATE           : "
        f"{positive / len(values) * 100:.2f}%"
    )

    print()
    print("=" * 110)
    print("CHRONOLOGICAL 3H RETURNS")
    print("=" * 110)

    for index, record in enumerate(
        records,
        start=1,
    ):
        print(
            f"{index:03d}  "
            f"{record['start_dt'].isoformat()}  "
            f"BARS={record['bars']:2d}  "
            f"3H={record['return_3h']:+.6f}%"
        )

    print()
    print("=" * 110)
    print("WORST 10 EPISODES")
    print("=" * 110)

    for index, record in enumerate(
        sorted(
            records,
            key=lambda item: item["return_3h"],
        )[:10],
        start=1,
    ):
        print(
            f"{index:02d}  "
            f"{record['start_dt'].isoformat()}  "
            f"BARS={record['bars']:2d}  "
            f"3H={record['return_3h']:+.6f}%"
        )

    print()
    print("=" * 110)
    print("BEST 10 EPISODES")
    print("=" * 110)

    for index, record in enumerate(
        sorted(
            records,
            key=lambda item: item["return_3h"],
            reverse=True,
        )[:10],
        start=1,
    ):
        print(
            f"{index:02d}  "
            f"{record['start_dt'].isoformat()}  "
            f"BARS={record['bars']:2d}  "
            f"3H={record['return_3h']:+.6f}%"
        )

    print()
    print("=" * 110)
    print("ROBUSTNESS CHECK — REMOVE EXTREMES")
    print("=" * 110)

    ordered_values = sorted(values)

    if len(ordered_values) >= 3:
        remove_best = ordered_values[:-1]
        remove_worst = ordered_values[1:]
        remove_both = ordered_values[1:-1]

        print(
            "REMOVE BEST 1 AVG       : "
            f"{sum(remove_best) / len(remove_best):+.6f}%"
        )
        print(
            "REMOVE WORST 1 AVG      : "
            f"{sum(remove_worst) / len(remove_worst):+.6f}%"
        )
        print(
            "REMOVE BEST+WORST AVG   : "
            f"{sum(remove_both) / len(remove_both):+.6f}%"
        )

    print()
    print("=" * 110)
    print("FINAL CHECK")
    print("=" * 110)

    expected_contexts = 108
    expected_episodes = 38

    context_check = (
        len(passed_bear)
        == expected_contexts
    )

    episode_check = (
        len(episodes)
        == expected_episodes
    )

    complete_check = (
        len(records)
        <= len(episodes)
        and len(records) > 0
    )

    print(
        "CONTEXT CHECK           :",
        "PASS" if context_check else "FAIL",
    )
    print(
        "EPISODE CHECK           :",
        "PASS" if episode_check else "FAIL",
    )
    print(
        "COMPLETE RETURN CHECK   :",
        "PASS" if complete_check else "FAIL",
    )

    print(
        "OVERALL CHECK           :",
        "PASS"
        if (
            context_check
            and episode_check
            and complete_check
        )
        else "FAIL",
    )

    print("=" * 110)


if __name__ == "__main__":
    run_audit()
