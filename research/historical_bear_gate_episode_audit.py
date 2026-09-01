"""
Historical BEAR Gate Episode Audit V1

Purpose:
- Identify production-gate PASSED BEAR contexts.
- Group consecutive 15-minute PASSED BEAR contexts into independent episodes.
- Evaluate forward BTC returns from the FIRST candle of each episode.
- Reduce overlap bias from candle-level BEAR Gate Effectiveness Audit V1.

Research only:
- No live trading
- No Strategy A modification
- No automatic threshold changes
"""

from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite

from replay.shadow_historical_data import fetch_klines_range
from research.historical_context_sequence import (
    build_context_sequence_from_dataframe,
)
from research.historical_regime_forward_return_audit import (
    FORWARD_HORIZONS,
)
from research.historical_regime_gate_distribution_audit import (
    classify_first_decision,
    classify_raw_structure,
)


START = datetime(2026, 6, 1, tzinfo=timezone.utc)
END = datetime(2026, 8, 21, tzinfo=timezone.utc)

INTERVAL_MS = 15 * 60 * 1000


def build_close_map(df):
    return {
        int(row["Time"]): float(row["Close"])
        for _, row in df.iterrows()
    }


def collect_passed_bear_contexts(contexts):
    passed = []

    for context in contexts:
        raw_structure = classify_raw_structure(context)

        if raw_structure != "BEAR":
            continue

        decision = classify_first_decision(
            context,
            raw_structure,
        )

        if decision == "BEAR":
            passed.append(context)

    return sorted(
        passed,
        key=lambda item: int(
            item["candle_time_ms"]
        ),
    )


def group_passed_bear_episodes(contexts):
    """
    Consecutive PASSED BEAR 15m contexts belong to one episode.
    """

    if not contexts:
        return []

    episodes = []
    current_episode = [contexts[0]]

    for context in contexts[1:]:
        previous_time = int(
            current_episode[-1]["candle_time_ms"]
        )
        current_time = int(
            context["candle_time_ms"]
        )

        if current_time - previous_time == INTERVAL_MS:
            current_episode.append(context)
        else:
            episodes.append(current_episode)
            current_episode = [context]

    episodes.append(current_episode)

    return episodes


def calculate_episode_forward_returns(
    episode,
    close_map,
):
    """
    Measure returns from the FIRST candle of the episode only.
    """

    first_context = episode[0]

    start_time_ms = int(
        first_context["candle_time_ms"]
    )
    entry_close = float(
        first_context["latest_close"]
    )

    returns = {}

    for label, bars_ahead in FORWARD_HORIZONS.items():
        future_time_ms = (
            start_time_ms
            + bars_ahead * INTERVAL_MS
        )

        future_close = close_map.get(
            future_time_ms
        )

        if future_close is None:
            returns[label] = None
            continue

        returns[label] = (
            future_close / entry_close - 1.0
        ) * 100.0

    return returns


def summarize(values):
    clean = [
        float(value)
        for value in values
        if value is not None
        and isfinite(float(value))
    ]

    if not clean:
        return {
            "count": 0,
            "average": 0.0,
            "up_rate": 0.0,
            "down_rate": 0.0,
        }

    count = len(clean)
    up_count = sum(value > 0 for value in clean)
    down_count = sum(value < 0 for value in clean)

    return {
        "count": count,
        "average": sum(clean) / count,
        "up_rate": up_count / count * 100.0,
        "down_rate": down_count / count * 100.0,
    }


def run_audit():
    start_ms = int(START.timestamp() * 1000)
    end_ms = int(END.timestamp() * 1000)

    print("=" * 110)
    print("HISTORICAL BEAR GATE EPISODE AUDIT V1")
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

    horizon_returns = {
        label: []
        for label in FORWARD_HORIZONS
    }

    episode_lengths = []

    for episode in episodes:
        episode_lengths.append(len(episode))

        returns = calculate_episode_forward_returns(
            episode,
            close_map,
        )

        for label, value in returns.items():
            if value is not None:
                horizon_returns[label].append(
                    value
                )

    print()
    print("KLINES                  :", len(df))
    print("MATURE CONTEXTS         :", len(contexts))
    print("PASSED BEAR CONTEXTS    :", len(passed_bear))
    print("BEAR PASSED EPISODES    :", len(episodes))

    print()
    print("=" * 110)
    print("EPISODE STRUCTURE")
    print("=" * 110)

    if episode_lengths:
        print(
            "SHORTEST EPISODE        :",
            min(episode_lengths),
            "bars",
        )
        print(
            "LONGEST EPISODE         :",
            max(episode_lengths),
            "bars",
        )
        print(
            "AVERAGE EPISODE         :",
            f"{sum(episode_lengths) / len(episode_lengths):.2f}",
            "bars",
        )
    else:
        print("NO EPISODES")

    print()
    print(
        "EPISODE BAR CONSERVATION:",
        sum(episode_lengths),
    )
    print(
        "EXPECTED PASSED BEAR    :",
        len(passed_bear),
    )
    print(
        "BAR CHECK               :",
        "PASS"
        if sum(episode_lengths) == len(passed_bear)
        else "FAIL",
    )

    print()
    print("=" * 110)
    print("EPISODE-START FORWARD RETURNS")
    print("=" * 110)

    for label in FORWARD_HORIZONS:
        stats = summarize(
            horizon_returns[label]
        )

        print(
            f"{label:<5} "
            f"N={stats['count']:4d}  "
            f"AVG={stats['average']:+.6f}%  "
            f"UP={stats['up_rate']:6.2f}%  "
            f"DOWN={stats['down_rate']:6.2f}%"
        )

    print()
    print("=" * 110)
    print("EPISODE LIST")
    print("=" * 110)

    for index, episode in enumerate(
        episodes,
        start=1,
    ):
        first_time = int(
            episode[0]["candle_time_ms"]
        )
        last_time = int(
            episode[-1]["candle_time_ms"]
        )

        first_dt = datetime.fromtimestamp(
            first_time / 1000,
            tz=timezone.utc,
        )
        last_dt = datetime.fromtimestamp(
            last_time / 1000,
            tz=timezone.utc,
        )

        print(
            f"{index:03d}  "
            f"{first_dt.isoformat()}  ->  "
            f"{last_dt.isoformat()}  "
            f"BARS={len(episode):3d}"
        )

    print()
    print("=" * 110)
    print("FINAL CHECK")
    print("=" * 110)

    expected_passed_bear = 108

    print(
        "PASSED BEAR CONTEXTS    :",
        len(passed_bear),
    )
    print(
        "EXPECTED                :",
        expected_passed_bear,
    )
    print(
        "CONTEXT CHECK           :",
        "PASS"
        if len(passed_bear) == expected_passed_bear
        else "FAIL",
    )

    print(
        "OVERALL CHECK           :",
        "PASS"
        if (
            len(passed_bear) == expected_passed_bear
            and sum(episode_lengths)
            == len(passed_bear)
        )
        else "FAIL",
    )

    print("=" * 110)


if __name__ == "__main__":
    run_audit()
