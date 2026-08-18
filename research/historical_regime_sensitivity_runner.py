"""
Historical Regime Sensitivity Runner V1

Evaluate historical Shadow outcomes under multiple
Market Regime threshold combinations.

Research only:
- No live trading
- No Strategy A modification
- No automatic parameter changes
- Historical closed-candle data only
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from replay.shadow_historical_data import timestamp_to_ms
from research.historical_context_snapshot import (
    load_historical_snapshot,
)
from research.historical_regime_sensitivity import (
    classify_with_thresholds,
    iter_threshold_combinations,
)


DEFAULT_INPUT = Path(
    "runtime/shadow/shadow_context_outcomes.jsonl"
)

INTERVAL_MS = 15 * 60 * 1000


def load_closed_rows(
    path: Path = DEFAULT_INPUT,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    if not path.exists():
        return rows

    with path.open("r", encoding="utf-8") as f:
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


def run_sensitivity() -> None:
    rows = load_closed_rows()

    combinations = list(
        iter_threshold_combinations()
    )

    snapshot_cache: dict[int, dict[str, Any]] = {}
    results = {}

    print("=" * 88)
    print("Historical Regime Threshold Sensitivity V1")
    print("=" * 88)
    print("Closed Shadow Records:", len(rows))
    print("Threshold Combinations:", len(combinations))
    print()

    for index, (
        volume_threshold,
        slope_threshold,
    ) in enumerate(combinations, 1):

        regime_counter: Counter[str] = Counter()

        performance = defaultdict(
            lambda: {
                "n": 0,
                "pnl": 0.0,
            }
        )

        errors = 0
        error_details: Counter[str] = Counter()

        for row in rows:
            timestamp = row["timestamp"]

            try:
                timestamp_ms = timestamp_to_ms(
                    timestamp
                )

                bucket_ms = (
                    timestamp_ms
                    // INTERVAL_MS
                    * INTERVAL_MS
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

                regime = classify_with_thresholds(
                    snapshot,
                    volume_threshold,
                    slope_threshold,
                )

                regime_counter[regime] += 1

                side = str(
                    row.get("side") or "UNKNOWN"
                )

                key = (
                    regime,
                    side,
                )

                pnl = float(
                    row.get("pnl") or 0.0
                )

                performance[key]["n"] += 1
                performance[key]["pnl"] += pnl

            except Exception as exc:
                errors += 1

                error_key = (
                    f"{type(exc).__name__}: "
                    f"{str(exc)[:120]}"
                )

                error_details[error_key] += 1

        result_key = (
            volume_threshold,
            slope_threshold,
        )

        results[result_key] = {
            "regime_counter": regime_counter,
            "performance": performance,
            "errors": errors,
            "error_details": error_details,
        }

        print(
            f"[{index:>2}/{len(combinations)}] "
            f"VOL={volume_threshold:<4} "
            f"SLOPE={slope_threshold:<6} "
            f"BULL={regime_counter['BULL']:<5} "
            f"BEAR={regime_counter['BEAR']:<5} "
            f"RANGE={regime_counter['RANGE']:<5} "
            f"ERR={errors}"
        )

    print()
    print("=" * 88)
    print("DETAILED PERFORMANCE")
    print("=" * 88)

    for (
        volume_threshold,
        slope_threshold,
    ), result in results.items():

        print()
        print(
            f"VOL={volume_threshold} "
            f"SLOPE={slope_threshold}"
        )

        for regime in (
            "BULL",
            "BEAR",
            "RANGE",
        ):
            for side in (
                "LONG",
                "SHORT",
            ):
                stats = result[
                    "performance"
                ].get(
                    (regime, side),
                    {
                        "n": 0,
                        "pnl": 0.0,
                    },
                )

                n = stats["n"]
                pnl = stats["pnl"]

                exp = (
                    pnl / n
                    if n
                    else 0.0
                )

                print(
                    f"  {regime:<5} "
                    f"{side:<5} "
                    f"N={n:<5} "
                    f"PnL={pnl:>10.4f} "
                    f"EXP={exp:>8.4f}"
                )

    print()
    print("=" * 88)
    print("CACHE")
    print("=" * 88)
    print(
        "Unique BTC 15m Buckets:",
        len(snapshot_cache),
    )


if __name__ == "__main__":
    run_sensitivity()
