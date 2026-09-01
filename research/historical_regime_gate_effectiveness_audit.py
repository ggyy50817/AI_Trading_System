"""
Historical Market Regime Gate Effectiveness Audit V1

Purpose:
- Test whether production Market Regime gates improve directional quality.
- Compare raw BULL / BEAR structures that PASS production gates
  against structures that are SUPPRESSED into RANGE.
- Evaluate forward returns at 15m / 45m / 90m / 3h.

Research only:
- No live trading
- No Strategy A modification
- No automatic threshold changes
"""

from __future__ import annotations

from collections import defaultdict
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


def calculate_context_forward_returns(context, close_map):
    timestamp_ms = int(context["candle_time_ms"])
    entry_close = float(context["latest_close"])

    results = {}

    for label, bars_ahead in FORWARD_HORIZONS.items():
        future_time_ms = timestamp_ms + bars_ahead * INTERVAL_MS
        future_close = close_map.get(future_time_ms)

        if future_close is None:
            results[label] = None
            continue

        forward_return = (
            (future_close - entry_close)
            / entry_close
        )

        results[label] = forward_return

    return results


def classify_gate_status(raw_structure, decision):
    if raw_structure == "BULL":
        if decision == "BULL":
            return "PASSED"
        return "SUPPRESSED"

    if raw_structure == "BEAR":
        if decision == "BEAR":
            return "PASSED"
        return "SUPPRESSED"

    return None


def summarize(values):
    clean = [
        float(value)
        for value in values
        if value is not None
        and isfinite(float(value))
    ]

    count = len(clean)

    if not count:
        return {
            "count": 0,
            "average": 0.0,
            "up_rate": 0.0,
            "down_rate": 0.0,
        }

    up = sum(value > 0 for value in clean)
    down = sum(value < 0 for value in clean)

    return {
        "count": count,
        "average": sum(clean) / count,
        "up_rate": up / count,
        "down_rate": down / count,
    }


def run_audit():
    start_ms = int(START.timestamp() * 1000)
    end_ms = int(END.timestamp() * 1000)

    print("=" * 110)
    print("HISTORICAL MARKET REGIME GATE EFFECTIVENESS AUDIT V1")
    print("=" * 110)

    df = fetch_klines_range(
        "BTC-USDT",
        start_ms,
        end_ms,
        interval="15m",
        page_limit=500,
    )

    contexts = build_context_sequence_from_dataframe(df)
    close_map = build_close_map(df)

    grouped_returns = defaultdict(
        lambda: defaultdict(list)
    )

    group_context_counts = defaultdict(int)

    for context in contexts:
        raw_structure = classify_raw_structure(context)

        if raw_structure not in ("BULL", "BEAR"):
            continue

        decision = classify_first_decision(
            context,
            raw_structure,
        )

        gate_status = classify_gate_status(
            raw_structure,
            decision,
        )

        if gate_status is None:
            continue

        group_key = (
            raw_structure,
            gate_status,
        )

        group_context_counts[group_key] += 1

        forward_returns = (
            calculate_context_forward_returns(
                context,
                close_map,
            )
        )

        for horizon, value in forward_returns.items():
            if value is not None:
                grouped_returns[group_key][horizon].append(
                    value
                )

    print()
    print("KLINES             :", len(df))
    print("MATURE CONTEXTS    :", len(contexts))

    print()
    print("=" * 110)
    print("GROUP CONTEXT COUNTS")
    print("=" * 110)

    for raw_structure in ("BULL", "BEAR"):
        for gate_status in ("PASSED", "SUPPRESSED"):
            key = (
                raw_structure,
                gate_status,
            )

            print(
                f"{raw_structure:<6} "
                f"{gate_status:<12} "
                f"{group_context_counts[key]:6d}"
            )

    print()
    print("=" * 110)
    print("FORWARD RETURN EFFECTIVENESS")
    print("=" * 110)

    for raw_structure in ("BULL", "BEAR"):
        print()
        print("-" * 110)
        print(f"RAW {raw_structure}")
        print("-" * 110)

        for gate_status in ("PASSED", "SUPPRESSED"):
            key = (
                raw_structure,
                gate_status,
            )

            print()
            print(
                f"{raw_structure} {gate_status} "
                f"— CONTEXTS "
                f"{group_context_counts[key]}"
            )

            for horizon in FORWARD_HORIZONS:
                stats = summarize(
                    grouped_returns[key][horizon]
                )

                average_pct = (
                    stats["average"] * 100
                )
                up_pct = (
                    stats["up_rate"] * 100
                )
                down_pct = (
                    stats["down_rate"] * 100
                )

                print(
                    f"{horizon:<5} "
                    f"N={stats['count']:5d}  "
                    f"AVG={average_pct:+.6f}%  "
                    f"UP={up_pct:6.2f}%  "
                    f"DOWN={down_pct:6.2f}%"
                )

    print()
    print("=" * 110)
    print("CONSERVATION")
    print("=" * 110)

    raw_bull_total = sum(
        group_context_counts[
            ("BULL", status)
        ]
        for status in (
            "PASSED",
            "SUPPRESSED",
        )
    )

    raw_bear_total = sum(
        group_context_counts[
            ("BEAR", status)
        ]
        for status in (
            "PASSED",
            "SUPPRESSED",
        )
    )

    print("RAW BULL TOTAL     :", raw_bull_total)
    print("EXPECTED RAW BULL  :", 2354)
    print(
        "BULL CHECK         :",
        "PASS"
        if raw_bull_total == 2354
        else "FAIL",
    )

    print()
    print("RAW BEAR TOTAL     :", raw_bear_total)
    print("EXPECTED RAW BEAR  :", 2140)
    print(
        "BEAR CHECK         :",
        "PASS"
        if raw_bear_total == 2140
        else "FAIL",
    )

    print()
    print(
        "OVERALL CHECK      :",
        "PASS"
        if (
            raw_bull_total == 2354
            and raw_bear_total == 2140
        )
        else "FAIL",
    )

    print("=" * 110)


if __name__ == "__main__":
    run_audit()
