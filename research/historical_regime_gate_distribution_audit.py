"""
Historical Market Regime Gate Distribution Audit V1

Purpose:
- Reproduce scanner/market_regime.py decision order on historical BTC 15m data.
- Measure how often ATR / Volume / MA20 Slope gates force RANGE.
- Compare final regime against raw MA20 / MA60 market structure.

Research only:
- No live trading
- No Strategy A modification
- No automatic threshold changes
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from replay.shadow_historical_data import fetch_klines_range
from research.historical_context_sequence import (
    build_context_sequence_from_dataframe,
)


START = datetime(2026, 6, 1, tzinfo=timezone.utc)
END = datetime(2026, 8, 21, tzinfo=timezone.utc)

ATR_THRESHOLD = 0.035
VOLUME_THRESHOLD = 0.8
SLOPE_THRESHOLD = 0.001


def classify_raw_structure(context):
    close = float(context["latest_close"])
    ma20 = float(context["ma20"])
    ma60 = float(context["ma60"])

    if close > ma20 > ma60:
        return "BULL"

    if close < ma20 < ma60:
        return "BEAR"

    return "MIXED"


def classify_first_decision(context, raw_structure):
    close = float(context["latest_close"])
    atr_pct = float(context["atr_pct"])
    volume_ratio = float(context["volume_ratio"])
    slope = float(context["ma20_slope"])

    # Keep this order identical to scanner/market_regime.py.
    if atr_pct > ATR_THRESHOLD:
        return "ATR_GATE"

    if volume_ratio < VOLUME_THRESHOLD:
        return "VOLUME_GATE"

    if abs(slope) < close * SLOPE_THRESHOLD:
        return "SLOPE_GATE"

    if raw_structure == "BULL":
        return "BULL"

    if raw_structure == "BEAR":
        return "BEAR"

    return "MIXED_RANGE"


def run_audit():
    start_ms = int(START.timestamp() * 1000)
    end_ms = int(END.timestamp() * 1000)

    print("=" * 100)
    print("HISTORICAL MARKET REGIME GATE DISTRIBUTION AUDIT V1")
    print("=" * 100)

    df = fetch_klines_range(
        "BTC-USDT",
        start_ms,
        end_ms,
        interval="15m",
        page_limit=500,
    )

    contexts = build_context_sequence_from_dataframe(df)

    structure = Counter()
    first_gate = Counter()
    suppressed_structure = Counter()

    for context in contexts:
        raw_structure = classify_raw_structure(context)
        structure[raw_structure] += 1

        decision = classify_first_decision(
            context,
            raw_structure,
        )
        first_gate[decision] += 1

        if decision in (
            "ATR_GATE",
            "VOLUME_GATE",
            "SLOPE_GATE",
        ):
            suppressed_structure[raw_structure] += 1

    total = len(contexts)

    def pct(value):
        return (
            value / total * 100
            if total
            else 0.0
        )

    print()
    print("KLINES             :", len(df))
    print("MATURE CONTEXTS    :", total)

    print()
    print("=" * 100)
    print("1. RAW MA STRUCTURE — BEFORE RANGE GATES")
    print("=" * 100)

    for key in ("BULL", "BEAR", "MIXED"):
        value = structure[key]
        print(
            f"{key:<20} "
            f"{value:6d}  "
            f"{pct(value):7.2f}%"
        )

    print()
    print("=" * 100)
    print("2. FIRST DECISION — EXACT PRODUCTION ORDER")
    print("=" * 100)

    for key in (
        "ATR_GATE",
        "VOLUME_GATE",
        "SLOPE_GATE",
        "MIXED_RANGE",
        "BULL",
        "BEAR",
    ):
        value = first_gate[key]
        print(
            f"{key:<20} "
            f"{value:6d}  "
            f"{pct(value):7.2f}%"
        )

    range_total = (
        first_gate["ATR_GATE"]
        + first_gate["VOLUME_GATE"]
        + first_gate["SLOPE_GATE"]
        + first_gate["MIXED_RANGE"]
    )

    print()
    print(
        f"{'TOTAL RANGE':<20} "
        f"{range_total:6d}  "
        f"{pct(range_total):7.2f}%"
    )
    print(
        f"{'FINAL BULL':<20} "
        f"{first_gate['BULL']:6d}  "
        f"{pct(first_gate['BULL']):7.2f}%"
    )
    print(
        f"{'FINAL BEAR':<20} "
        f"{first_gate['BEAR']:6d}  "
        f"{pct(first_gate['BEAR']):7.2f}%"
    )

    print()
    print("=" * 100)
    print("3. STRUCTURE SUPPRESSED BY ATR / VOLUME / SLOPE GATES")
    print("=" * 100)

    suppressed_total = sum(
        suppressed_structure.values()
    )

    for key in ("BULL", "BEAR", "MIXED"):
        value = suppressed_structure[key]
        percentage = (
            value / suppressed_total * 100
            if suppressed_total
            else 0.0
        )

        print(
            f"{key:<20} "
            f"{value:6d}  "
            f"{percentage:7.2f}%"
        )

    print()
    print("SUPPRESSED TOTAL    :", suppressed_total)

    print()
    print("=" * 100)
    print("CONSERVATION")
    print("=" * 100)

    decision_total = sum(first_gate.values())

    print("CONTEXTS            :", total)
    print("DECISIONS           :", decision_total)
    print(
        "CHECK               :",
        "PASS"
        if total == decision_total
        else "FAIL",
    )

    print("=" * 100)


if __name__ == "__main__":
    run_audit()
