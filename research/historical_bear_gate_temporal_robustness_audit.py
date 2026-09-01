"""
Historical BEAR Gate Temporal Robustness Audit V1

Purpose:
- Test whether the PASSED BEAR late-entry / rebound pattern is
  concentrated in one calendar period.
- Reuse the 3h non-overlapping PASSED BEAR episodes.
- Compare PRE-3H and POST-3H behavior by month and chronological half.

Research only:
- No live trading
- No Strategy A modification
- No automatic threshold changes
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

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
from research.historical_bear_gate_independent_episode_audit import (
    select_non_overlapping_episodes,
)
from research.historical_bear_pre_regime_path_audit import (
    backward_return,
)
from research.historical_bear_gate_pre_move_audit import (
    summarize,
)


START = datetime(2026, 6, 1, tzinfo=timezone.utc)
END = datetime(2026, 8, 21, tzinfo=timezone.utc)

PRE_3H_CANDLES = 12


def build_records(df, selected, close_map):
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

        current_index = index_by_time[start_time_ms]

        try:
            pre_3h = backward_return(
                closes,
                current_index,
                PRE_3H_CANDLES,
            )
        except ValueError:
            continue

        forward_returns = calculate_episode_forward_returns(
            episode,
            close_map,
        )

        post_3h = forward_returns.get("3h")

        if post_3h is None:
            continue

        start_dt = datetime.fromtimestamp(
            start_time_ms / 1000,
            tz=timezone.utc,
        )

        records.append(
            {
                "start_time_ms": start_time_ms,
                "start_dt": start_dt,
                "month": start_dt.strftime("%Y-%m"),
                "pre_3h": float(pre_3h),
                "post_3h": float(post_3h),
            }
        )

    return records


def print_group_summary(name, records):
    print()
    print(f"--- {name} ---")

    if not records:
        print("NO DATA")
        return

    pre_values = [
        record["pre_3h"]
        for record in records
    ]

    post_values = [
        record["post_3h"]
        for record in records
    ]

    pre_stats = summarize(pre_values)
    post_stats = summarize(post_values)

    reversal_count = sum(
        record["pre_3h"] < 0
        and record["post_3h"] > 0
        for record in records
    )

    continuation_count = sum(
        record["pre_3h"] < 0
        and record["post_3h"] < 0
        for record in records
    )

    print(f"N                            : {len(records)}")

    print(
        f"PRE-3H AVG                   : "
        f"{pre_stats['average']:+.6f}%"
    )
    print(
        f"PRE-3H MEDIAN                : "
        f"{pre_stats['median']:+.6f}%"
    )
    print(
        f"PRE-3H DOWN                  : "
        f"{pre_stats['negative']} "
        f"({pre_stats['negative_rate']:.2f}%)"
    )

    print(
        f"POST-3H AVG                  : "
        f"{post_stats['average']:+.6f}%"
    )
    print(
        f"POST-3H MEDIAN               : "
        f"{post_stats['median']:+.6f}%"
    )
    print(
        f"POST-3H UP                   : "
        f"{post_stats['positive']} "
        f"({post_stats['positive_rate']:.2f}%)"
    )
    print(
        f"POST-3H DOWN                 : "
        f"{post_stats['negative']} "
        f"({post_stats['negative_rate']:.2f}%)"
    )

    print(
        f"DOWN -> UP                   : "
        f"{reversal_count} "
        f"({reversal_count / len(records) * 100:.2f}%)"
    )
    print(
        f"DOWN -> DOWN                 : "
        f"{continuation_count} "
        f"({continuation_count / len(records) * 100:.2f}%)"
    )


def run_audit():
    start_ms = int(START.timestamp() * 1000)
    end_ms = int(END.timestamp() * 1000)

    print("=" * 110)
    print("HISTORICAL BEAR GATE TEMPORAL ROBUSTNESS AUDIT V1")
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

    records = build_records(
        df,
        selected,
        close_map,
    )

    print()
    print("KLINES                       :", len(df))
    print("MATURE CONTEXTS              :", len(contexts))
    print("PASSED BEAR CONTEXTS         :", len(passed_bear))
    print("ORIGINAL BEAR EPISODES       :", len(episodes))
    print("NON-OVERLAPPING EPISODES     :", len(selected))
    print("EXCLUDED OVERLAP EPISODES    :", len(excluded))
    print("COMPLETE TEMPORAL RECORDS    :", len(records))

    print()
    print("=" * 110)
    print("OVERALL REFERENCE")
    print("=" * 110)

    print_group_summary(
        "ALL NON-OVERLAPPING EPISODES",
        records,
    )

    print()
    print("=" * 110)
    print("CALENDAR MONTH ROBUSTNESS")
    print("=" * 110)

    by_month = defaultdict(list)

    for record in records:
        by_month[record["month"]].append(record)

    for month in sorted(by_month):
        print_group_summary(
            month,
            by_month[month],
        )

    print()
    print("=" * 110)
    print("CHRONOLOGICAL HALF ROBUSTNESS")
    print("=" * 110)

    ordered_records = sorted(
        records,
        key=lambda item: item["start_time_ms"],
    )

    midpoint = (
        len(ordered_records) + 1
    ) // 2

    first_half = ordered_records[:midpoint]
    second_half = ordered_records[midpoint:]

    print_group_summary(
        "FIRST HALF",
        first_half,
    )

    print_group_summary(
        "SECOND HALF",
        second_half,
    )

    print()
    print("=" * 110)
    print("MONTH COUNTS")
    print("=" * 110)

    month_total = 0

    for month in sorted(by_month):
        count = len(by_month[month])
        month_total += count

        print(
            f"{month}                       : "
            f"{count}"
        )

    print(
        "MONTH TOTAL                  :",
        month_total,
    )

    print()
    print("=" * 110)
    print("CHRONOLOGICAL RECORDS")
    print("=" * 110)

    for index, record in enumerate(
        ordered_records,
        start=1,
    ):
        half = (
            "FIRST"
            if index <= midpoint
            else "SECOND"
        )

        path = (
            "DOWN->UP"
            if (
                record["pre_3h"] < 0
                and record["post_3h"] > 0
            )
            else "DOWN->DOWN"
            if (
                record["pre_3h"] < 0
                and record["post_3h"] < 0
            )
            else "OTHER"
        )

        print(
            f"{index:03d}  "
            f"{record['start_dt'].isoformat()}  "
            f"HALF={half:6s}  "
            f"PRE3H={record['pre_3h']:+.6f}%  "
            f"POST3H={record['post_3h']:+.6f}%  "
            f"{path}"
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

    month_check = (
        month_total == len(records)
    )

    half_check = (
        len(first_half)
        + len(second_half)
        == len(records)
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
    print(
        "MONTH CONSERVATION CHECK     :",
        "PASS" if month_check else "FAIL",
    )
    print(
        "HALF CONSERVATION CHECK      :",
        "PASS" if half_check else "FAIL",
    )

    overall_check = (
        context_check
        and episode_check
        and selected_check
        and complete_check
        and month_check
        and half_check
    )

    print(
        "OVERALL CHECK                :",
        "PASS" if overall_check else "FAIL",
    )

    print("=" * 110)


if __name__ == "__main__":
    run_audit()
