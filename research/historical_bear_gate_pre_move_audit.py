"""
Historical BEAR Gate Pre-Move Audit V1

Purpose:
- Measure BTC price movement BEFORE each selected non-overlapping
  PASSED BEAR episode.
- Test whether the production BEAR gate tends to appear only after
  BTC has already experienced a meaningful decline.
- Compare pre-move behavior with the known post-signal 3h behavior.

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
    collect_passed_bear_contexts,
    group_passed_bear_episodes,
    calculate_episode_forward_returns,
    build_close_map,
)
from research.historical_bear_gate_independent_episode_audit import (
    select_non_overlapping_episodes,
)
from research.historical_bear_pre_regime_path_audit import (
    backward_return,
)


START = datetime(2026, 6, 1, tzinfo=timezone.utc)
END = datetime(2026, 8, 21, tzinfo=timezone.utc)

PRE_WINDOWS = (
    (3, "45m"),
    (6, "90m"),
    (12, "3h"),
    (24, "6h"),
)


def percentile(values, q):
    return float(
        np.percentile(
            np.asarray(values, dtype=float),
            q,
        )
    )


def summarize(values):
    if not values:
        return None

    positive = sum(
        value > 0
        for value in values
    )

    negative = sum(
        value < 0
        for value in values
    )

    zero = sum(
        value == 0
        for value in values
    )

    return {
        "n": len(values),
        "average": sum(values) / len(values),
        "median": percentile(values, 50),
        "p25": percentile(values, 25),
        "p75": percentile(values, 75),
        "minimum": min(values),
        "maximum": max(values),
        "positive": positive,
        "negative": negative,
        "zero": zero,
        "positive_rate": (
            positive / len(values) * 100.0
        ),
        "negative_rate": (
            negative / len(values) * 100.0
        ),
    }


def run_audit():
    start_ms = int(START.timestamp() * 1000)
    end_ms = int(END.timestamp() * 1000)

    print("=" * 110)
    print("HISTORICAL BEAR GATE PRE-MOVE AUDIT V1")
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

    selected, excluded = select_non_overlapping_episodes(
        episodes
    )

    close_map = build_close_map(df)

    ordered_df = (
        df.sort_values("Time")
        .drop_duplicates(
            subset=["Time"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    closes = [
        float(value)
        for value in ordered_df["Close"]
    ]

    index_by_time = {
        int(row["Time"]): int(index)
        for index, row in ordered_df.iterrows()
    }

    records = []

    for episode in selected:
        start_time_ms = int(
            episode[0]["candle_time_ms"]
        )

        if start_time_ms not in index_by_time:
            continue

        current_index = index_by_time[
            start_time_ms
        ]

        pre_returns = {}

        complete = True

        for candles, label in PRE_WINDOWS:
            try:
                value = backward_return(
                    closes,
                    current_index,
                    candles,
                )
            except ValueError:
                complete = False
                break

            pre_returns[label] = float(value)

        if not complete:
            continue

        forward_returns = (
            calculate_episode_forward_returns(
                episode,
                close_map,
            )
        )

        post_3h = forward_returns.get("3h")

        if post_3h is None:
            continue

        records.append(
            {
                "start_time_ms": start_time_ms,
                "start_dt": datetime.fromtimestamp(
                    start_time_ms / 1000,
                    tz=timezone.utc,
                ),
                "bars": len(episode),
                "pre_returns": pre_returns,
                "post_3h": float(post_3h),
            }
        )

    print()
    print("KLINES                       :", len(df))
    print("MATURE CONTEXTS              :", len(contexts))
    print("PASSED BEAR CONTEXTS         :", len(passed_bear))
    print("ORIGINAL BEAR EPISODES       :", len(episodes))
    print("NON-OVERLAPPING EPISODES     :", len(selected))
    print("COMPLETE PRE/POST RECORDS    :", len(records))

    print()
    print("=" * 110)
    print("PRE-MOVE DISTRIBUTION")
    print("=" * 110)

    for _, label in PRE_WINDOWS:
        values = [
            record["pre_returns"][label]
            for record in records
        ]

        stats = summarize(values)

        print()
        print(f"--- PRE {label} ---")

        if stats is None:
            print("NO DATA")
            continue

        print(
            f"N                            : "
            f"{stats['n']}"
        )
        print(
            f"AVERAGE                      : "
            f"{stats['average']:+.6f}%"
        )
        print(
            f"MEDIAN                       : "
            f"{stats['median']:+.6f}%"
        )
        print(
            f"P25                          : "
            f"{stats['p25']:+.6f}%"
        )
        print(
            f"P75                          : "
            f"{stats['p75']:+.6f}%"
        )
        print(
            f"MIN                          : "
            f"{stats['minimum']:+.6f}%"
        )
        print(
            f"MAX                          : "
            f"{stats['maximum']:+.6f}%"
        )
        print(
            f"UP                           : "
            f"{stats['positive']} "
            f"({stats['positive_rate']:.2f}%)"
        )
        print(
            f"DOWN                         : "
            f"{stats['negative']} "
            f"({stats['negative_rate']:.2f}%)"
        )
        print(
            f"FLAT                         : "
            f"{stats['zero']}"
        )

    print()
    print("=" * 110)
    print("POST-SIGNAL 3H REFERENCE")
    print("=" * 110)

    post_values = [
        record["post_3h"]
        for record in records
    ]

    post_stats = summarize(
        post_values
    )

    if post_stats is not None:
        print(
            f"N                            : "
            f"{post_stats['n']}"
        )
        print(
            f"AVERAGE                      : "
            f"{post_stats['average']:+.6f}%"
        )
        print(
            f"MEDIAN                       : "
            f"{post_stats['median']:+.6f}%"
        )
        print(
            f"UP                           : "
            f"{post_stats['positive']} "
            f"({post_stats['positive_rate']:.2f}%)"
        )
        print(
            f"DOWN                         : "
            f"{post_stats['negative']} "
            f"({post_stats['negative_rate']:.2f}%)"
        )

    print()
    print("=" * 110)
    print("EPISODE PRE-MOVE PATHS")
    print("=" * 110)

    for index, record in enumerate(
        records,
        start=1,
    ):
        pre = record["pre_returns"]

        print(
            f"{index:03d}  "
            f"{record['start_dt'].isoformat()}  "
            f"BARS={record['bars']:2d}  "
            f"PRE45M={pre['45m']:+.6f}%  "
            f"PRE90M={pre['90m']:+.6f}%  "
            f"PRE3H={pre['3h']:+.6f}%  "
            f"PRE6H={pre['6h']:+.6f}%  "
            f"POST3H={record['post_3h']:+.6f}%"
        )

    print()
    print("=" * 110)
    print("PRE-3H DOWN -> POST-3H BEHAVIOR")
    print("=" * 110)

    pre3h_down_records = [
        record
        for record in records
        if record["pre_returns"]["3h"] < 0
    ]

    pre3h_down_post_values = [
        record["post_3h"]
        for record in pre3h_down_records
    ]

    reversal_stats = summarize(
        pre3h_down_post_values
    )

    print(
        "PRE-3H DOWN EPISODES         :",
        len(pre3h_down_records),
    )

    if reversal_stats is not None:
        print(
            f"POST-3H AVG                 : "
            f"{reversal_stats['average']:+.6f}%"
        )
        print(
            f"POST-3H MEDIAN              : "
            f"{reversal_stats['median']:+.6f}%"
        )
        print(
            f"POST-3H UP                  : "
            f"{reversal_stats['positive']} "
            f"({reversal_stats['positive_rate']:.2f}%)"
        )
        print(
            f"POST-3H DOWN                : "
            f"{reversal_stats['negative']} "
            f"({reversal_stats['negative_rate']:.2f}%)"
        )

    print()
    print("=" * 110)
    print("FINAL CHECK")
    print("=" * 110)

    context_check = (
        len(passed_bear) == 108
    )

    episode_check = (
        len(episodes) == 38
    )

    selected_check = (
        len(selected) == 25
    )

    complete_check = (
        len(records) == len(selected)
    )

    print(
        "CONTEXT CHECK                :",
        "PASS" if context_check else "FAIL",
    )
    print(
        "ORIGINAL EPISODE CHECK       :",
        "PASS" if episode_check else "FAIL",
    )
    print(
        "NON-OVERLAP EPISODE CHECK    :",
        "PASS" if selected_check else "FAIL",
    )
    print(
        "COMPLETE RECORD CHECK        :",
        "PASS" if complete_check else "FAIL",
    )

    overall_check = (
        context_check
        and episode_check
        and selected_check
        and complete_check
    )

    print(
        "OVERALL CHECK                :",
        "PASS" if overall_check else "FAIL",
    )

    print("=" * 110)


if __name__ == "__main__":
    run_audit()
