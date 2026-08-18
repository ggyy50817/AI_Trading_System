"""
Historical Regime Audit V1

Audit historical Shadow market regimes and explain
why records are classified as RANGE.

Research only:
- No live trading
- No Strategy A modification
- No automatic parameter changes
- Historical closed-candle data only
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from research.historical_context_snapshot import (
    load_historical_snapshot,
)
from research.historical_market_regime import (
    classify_historical_regime,
)


DEFAULT_INPUT = Path(
    "runtime/shadow/shadow_context_outcomes.jsonl"
)


def load_closed_rows(
    path: Path = DEFAULT_INPUT,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    if not path.exists():
        return rows

    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue

            if row.get("status") != "CLOSED":
                continue

            if not row.get("timestamp"):
                continue

            rows.append(row)

    return rows


def get_range_reason(
    snapshot: dict[str, Any],
) -> str:
    """
    Return the first Market Regime V1 gate that
    forces the snapshot into RANGE.
    """

    latest_close = float(
        snapshot["latest_close"]
    )

    latest_ma20 = float(
        snapshot["ma20"]
    )

    latest_ma60 = float(
        snapshot["ma60"]
    )

    atr_pct = float(
        snapshot["atr_pct"]
    )

    volume_ratio = float(
        snapshot["volume_ratio"]
    )

    ma20_slope = float(
        snapshot["ma20_slope"]
    )

    if atr_pct > 0.035:
        return "HIGH_ATR"

    if volume_ratio < 0.8:
        return "LOW_VOLUME"

    if (
        abs(ma20_slope)
        < latest_close * 0.001
    ):
        return "LOW_MA20_SLOPE"

    bull_alignment = (
        latest_close > latest_ma20
        and latest_ma20 > latest_ma60
    )

    bear_alignment = (
        latest_close < latest_ma20
        and latest_ma20 < latest_ma60
    )

    if not bull_alignment and not bear_alignment:
        return "MA_ALIGNMENT"

    return "NOT_RANGE"


def run_audit() -> None:
    rows = load_closed_rows()

    regime_counter: Counter[str] = Counter()
    range_reason_counter: Counter[str] = Counter()
    original_counter: Counter[str] = Counter()

    errors: Counter[str] = Counter()

    # Multiple Shadow trades can share the same historical
    # BTC decision context. Cache snapshots by 15-minute bucket.
    snapshot_cache: dict[
        int,
        dict[str, Any],
    ] = {}

    print("=" * 80)
    print("Historical Regime Audit V1")
    print("=" * 80)
    print("Closed Shadow Records:", len(rows))
    print()

    for i, row in enumerate(rows, 1):
        timestamp = row["timestamp"]

        try:
            from replay.shadow_historical_data import (
                timestamp_to_ms,
            )

            timestamp_ms = timestamp_to_ms(
                timestamp
            )

            bucket_ms = (
                timestamp_ms
                // (15 * 60 * 1000)
                * (15 * 60 * 1000)
            )

            if bucket_ms not in snapshot_cache:
                snapshot_cache[bucket_ms] = (
                    load_historical_snapshot(
                        timestamp
                    )
                )

            snapshot = snapshot_cache[
                bucket_ms
            ]

            regime = classify_historical_regime(
                snapshot
            )

            regime_counter[regime] += 1

            original_regime = (
                row.get("market_regime")
                or "UNKNOWN"
            )

            original_counter[
                str(original_regime)
            ] += 1

            if regime == "RANGE":
                reason = get_range_reason(
                    snapshot
                )

                range_reason_counter[
                    reason
                ] += 1

        except Exception as exc:
            error_key = (
                f"{type(exc).__name__}: "
                f"{str(exc)[:120]}"
            )

            errors[error_key] += 1

        if i % 250 == 0 or i == len(rows):
            print(
                f"Progress {i}/{len(rows)}"
            )

    print()
    print("=" * 80)
    print("HISTORICAL REGIME")
    print("=" * 80)

    total_classified = sum(
        regime_counter.values()
    )

    for regime in (
        "BULL",
        "BEAR",
        "RANGE",
    ):
        count = regime_counter[regime]

        pct = (
            count / total_classified * 100
            if total_classified
            else 0.0
        )

        print(
            f"{regime:<10} "
            f"N={count:<6} "
            f"{pct:6.2f}%"
        )

    print()
    print("=" * 80)
    print("WHY RANGE")
    print("=" * 80)

    for reason, count in (
        range_reason_counter
        .most_common()
    ):
        pct = (
            count
            / regime_counter["RANGE"]
            * 100
            if regime_counter["RANGE"]
            else 0.0
        )

        print(
            f"{reason:<20} "
            f"N={count:<6} "
            f"{pct:6.2f}%"
        )

    print()
    print("=" * 80)
    print("ORIGINAL RECORDED REGIME")
    print("=" * 80)

    for regime, count in (
        original_counter
        .most_common()
    ):
        print(
            f"{regime:<10} "
            f"N={count}"
        )

    print()
    print("=" * 80)
    print("CACHE / ERRORS")
    print("=" * 80)

    print(
        "Unique BTC 15m Buckets:",
        len(snapshot_cache),
    )

    print(
        "Classified:",
        total_classified,
    )

    print(
        "Errors:",
        sum(errors.values()),
    )

    if errors:
        print()
        for error, count in errors.most_common():
            print(
                f"{count:>5} x {error}"
            )


if __name__ == "__main__":
    run_audit()