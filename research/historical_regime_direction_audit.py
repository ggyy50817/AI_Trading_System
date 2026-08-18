"""
Historical Regime Direction Audit V1

Investigate Shadow performance by historical BTC regime
and trade direction.

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
)


DEFAULT_INPUT = Path(
    "runtime/shadow/shadow_context_outcomes.jsonl"
)

INTERVAL_MS = 15 * 60 * 1000

# Research baseline only.
# These are NOT production parameter changes.
VOLUME_THRESHOLD = 0.0
SLOPE_THRESHOLD = 0.0


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


def make_stats() -> dict[str, Any]:
    return {
        "n": 0,
        "wins": 0,
        "losses": 0,
        "pnl": 0.0,
        "gross_profit": 0.0,
        "gross_loss": 0.0,
        "win_pnl": 0.0,
        "loss_pnl": 0.0,
        "results": Counter(),
    }


def run_audit() -> None:
    rows = load_closed_rows()

    snapshot_cache: dict[int, dict[str, Any]] = {}

    performance = defaultdict(make_stats)

    regime_counter: Counter[str] = Counter()
    errors: Counter[str] = Counter()

    print("=" * 92)
    print("Historical Regime Direction Audit V1")
    print("=" * 92)
    print("Closed Shadow Records:", len(rows))
    print("Volume Threshold:", VOLUME_THRESHOLD)
    print("Slope Threshold :", SLOPE_THRESHOLD)
    print()

    for index, row in enumerate(rows, 1):
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
                VOLUME_THRESHOLD,
                SLOPE_THRESHOLD,
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
                row.get("realized_pnl") or 0.0
            )

            result = str(
                row.get("result") or "UNKNOWN"
            )

            stats = performance[key]

            stats["n"] += 1
            stats["pnl"] += pnl
            stats["results"][result] += 1

            if pnl > 0:
                stats["wins"] += 1
                stats["gross_profit"] += pnl
                stats["win_pnl"] += pnl

            elif pnl < 0:
                stats["losses"] += 1
                stats["gross_loss"] += pnl
                stats["loss_pnl"] += pnl

        except Exception as exc:
            error_key = (
                f"{type(exc).__name__}: "
                f"{str(exc)[:120]}"
            )

            errors[error_key] += 1

        if index % 500 == 0 or index == len(rows):
            print(
                f"Progress {index}/{len(rows)}"
            )

    print()
    print("=" * 92)
    print("REGIME DISTRIBUTION")
    print("=" * 92)

    for regime in ("BULL", "BEAR", "RANGE"):
        print(
            f"{regime:<8} "
            f"N={regime_counter[regime]}"
        )

    print()
    print("=" * 92)
    print("REGIME x DIRECTION PERFORMANCE")
    print("=" * 92)

    for regime in ("BULL", "BEAR", "RANGE"):
        for side in ("LONG", "SHORT"):
            stats = performance[
                (regime, side)
            ]

            n = stats["n"]
            wins = stats["wins"]
            losses = stats["losses"]
            pnl = stats["pnl"]

            win_rate = (
                wins / n * 100
                if n
                else 0.0
            )

            expectancy = (
                pnl / n
                if n
                else 0.0
            )

            gross_profit = stats[
                "gross_profit"
            ]

            gross_loss_abs = abs(
                stats["gross_loss"]
            )

            if gross_loss_abs > 0:
                profit_factor = (
                    gross_profit
                    / gross_loss_abs
                )
                pf_text = (
                    f"{profit_factor:.3f}"
                )
            elif gross_profit > 0:
                pf_text = "INF"
            else:
                pf_text = "0.000"

            avg_win = (
                stats["win_pnl"] / wins
                if wins
                else 0.0
            )

            avg_loss = (
                stats["loss_pnl"] / losses
                if losses
                else 0.0
            )

            print()
            print(
                f"{regime} x {side}"
            )

            print(
                f"  N            = {n}"
            )
            print(
                f"  W / L        = "
                f"{wins} / {losses}"
            )
            print(
                f"  Win Rate     = "
                f"{win_rate:.2f}%"
            )
            print(
                f"  PnL          = "
                f"{pnl:.4f}"
            )
            print(
                f"  EXP          = "
                f"{expectancy:.4f}"
            )
            print(
                f"  PF           = "
                f"{pf_text}"
            )
            print(
                f"  Avg Win      = "
                f"{avg_win:.4f}"
            )
            print(
                f"  Avg Loss     = "
                f"{avg_loss:.4f}"
            )

            result_counter = stats[
                "results"
            ]

            print(
                "  Results      = "
                f"{dict(result_counter)}"
            )

    print()
    print("=" * 92)
    print("CACHE / ERRORS")
    print("=" * 92)

    print(
        "Unique BTC 15m Buckets:",
        len(snapshot_cache),
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
