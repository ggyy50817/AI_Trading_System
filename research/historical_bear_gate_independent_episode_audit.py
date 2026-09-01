"""
Historical BEAR Gate Independent Episode Audit V1

Purpose:
- Start from PASSED BEAR episodes.
- Remove episode starts whose 3h forward observation windows overlap
  with an already selected episode.
- Recalculate 3h forward-return distribution on the reduced sample.

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

THREE_HOURS_MS = 3 * 60 * 60 * 1000


def select_non_overlapping_episodes(episodes):
    """
    Greedy chronological selection.

    Keep the earliest episode.
    A later episode is eligible only when its START timestamp is
    at or after the end of the previous selected 3h observation window.

    Boundary rule:
        start == previous_start + 3h
    is allowed because the forward windows do not overlap.
    """

    ordered = sorted(
        episodes,
        key=lambda episode: int(
            episode[0]["candle_time_ms"]
        ),
    )

    selected = []
    excluded = []

    next_allowed_time_ms = None

    for episode in ordered:
        start_time_ms = int(
            episode[0]["candle_time_ms"]
        )

        if (
            next_allowed_time_ms is None
            or start_time_ms >= next_allowed_time_ms
        ):
            selected.append(episode)

            next_allowed_time_ms = (
                start_time_ms
                + THREE_HOURS_MS
            )
        else:
            excluded.append(episode)

    return selected, excluded


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
    print("HISTORICAL BEAR GATE INDEPENDENT EPISODE AUDIT V1")
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

    records = []

    for episode in selected:
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

        records.append(
            {
                "start_time_ms": start_time_ms,
                "start_dt": datetime.fromtimestamp(
                    start_time_ms / 1000,
                    tz=timezone.utc,
                ),
                "bars": len(episode),
                "return_3h": float(return_3h),
            }
        )

    values = [
        record["return_3h"]
        for record in records
    ]

    print()
    print("KLINES                       :", len(df))
    print("MATURE CONTEXTS              :", len(contexts))
    print("PASSED BEAR CONTEXTS         :", len(passed_bear))
    print("ORIGINAL BEAR EPISODES       :", len(episodes))
    print("NON-OVERLAPPING EPISODES     :", len(selected))
    print("EXCLUDED OVERLAP EPISODES    :", len(excluded))
    print("COMPLETE 3H RETURNS          :", len(records))

    print()
    print("=" * 110)
    print("NON-OVERLAP CONSERVATION")
    print("=" * 110)

    print(
        "SELECTED + EXCLUDED          :",
        len(selected) + len(excluded),
    )
    print(
        "EXPECTED ORIGINAL EPISODES   :",
        len(episodes),
    )

    conservation_check = (
        len(selected)
        + len(excluded)
        == len(episodes)
    )

    print(
        "CONSERVATION CHECK           :",
        "PASS" if conservation_check else "FAIL",
    )

    print()
    print("=" * 110)
    print("3H FORWARD RETURN DISTRIBUTION")
    print("=" * 110)

    if not values:
        print("NO COMPLETE 3H RETURNS")
        return

    average = sum(values) / len(values)
    med = percentile(values, 50)
    p25 = percentile(values, 25)
    p75 = percentile(values, 75)

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

    print(f"COUNT                        : {len(values)}")
    print(f"AVERAGE                      : {average:+.6f}%")
    print(f"MEDIAN                       : {med:+.6f}%")
    print(f"P25                          : {p25:+.6f}%")
    print(f"P75                          : {p75:+.6f}%")
    print(f"MIN                          : {min(values):+.6f}%")
    print(f"MAX                          : {max(values):+.6f}%")

    print()
    print(f"POSITIVE                     : {positive}")
    print(f"NEGATIVE                     : {negative}")
    print(f"ZERO                         : {zero}")
    print(
        "POSITIVE RATE                : "
        f"{positive / len(values) * 100:.2f}%"
    )

    print()
    print("=" * 110)
    print("SELECTED NON-OVERLAPPING EPISODES")
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
    print("ROBUSTNESS CHECK — REMOVE EXTREMES")
    print("=" * 110)

    ordered_values = sorted(values)

    if len(ordered_values) >= 3:
        remove_best = ordered_values[:-1]
        remove_worst = ordered_values[1:]
        remove_both = ordered_values[1:-1]

        print(
            "REMOVE BEST 1 AVG            : "
            f"{sum(remove_best) / len(remove_best):+.6f}%"
        )
        print(
            "REMOVE WORST 1 AVG           : "
            f"{sum(remove_worst) / len(remove_worst):+.6f}%"
        )
        print(
            "REMOVE BEST+WORST AVG        : "
            f"{sum(remove_both) / len(remove_both):+.6f}%"
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

    complete_check = (
        len(records) == len(selected)
    )

    overlap_check = True

    selected_start_times = [
        int(
            episode[0]["candle_time_ms"]
        )
        for episode in selected
    ]

    for previous, current in zip(
        selected_start_times,
        selected_start_times[1:],
    ):
        if current - previous < THREE_HOURS_MS:
            overlap_check = False
            break

    print(
        "CONTEXT CHECK                :",
        "PASS" if context_check else "FAIL",
    )
    print(
        "ORIGINAL EPISODE CHECK       :",
        "PASS" if episode_check else "FAIL",
    )
    print(
        "CONSERVATION CHECK           :",
        "PASS" if conservation_check else "FAIL",
    )
    print(
        "3H NON-OVERLAP CHECK         :",
        "PASS" if overlap_check else "FAIL",
    )
    print(
        "COMPLETE RETURN CHECK        :",
        "PASS" if complete_check else "FAIL",
    )

    overall_check = (
        context_check
        and episode_check
        and conservation_check
        and overlap_check
        and complete_check
    )

    print(
        "OVERALL CHECK                :",
        "PASS" if overall_check else "FAIL",
    )

    print("=" * 110)


if __name__ == "__main__":
    run_audit()
