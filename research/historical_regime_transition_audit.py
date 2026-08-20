"""
Historical Regime Transition Audit V1

Analyze Shadow performance by:
Historical BTC Regime x Direction x Regime Age.

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

from replay.shadow_historical_data import (
    timestamp_to_ms,
)
from research.historical_context_sequence import (
    load_historical_context_sequence,
)
from research.historical_regime_sensitivity import (
    classify_with_thresholds,
)
from research.historical_regime_transition import (
    calculate_regime_age,
    regime_age_bucket,
)


DEFAULT_INPUT = Path(
    "runtime/shadow/shadow_context_outcomes.jsonl"
)

INTERVAL_MS = 15 * 60 * 1000
SEQUENCE_LENGTH = 80

# Research baseline only.
# These are NOT production parameter changes.
VOLUME_THRESHOLD = 0.0
SLOPE_THRESHOLD = 0.0


def classify_research_regime(
    snapshot: dict[str, Any],
) -> str:
    return classify_with_thresholds(
        snapshot,
        VOLUME_THRESHOLD,
        SLOPE_THRESHOLD,
    )

AGE_BUCKETS = (
    "1",
    "2-3",
    "4-8",
    "9-20",
    "21-40",
    "41-79",
    "80+",
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


def print_stats(
    regime: str,
    side: str,
    bucket: str,
    stats: dict[str, Any],
) -> None:
    n = stats["n"]

    if n == 0:
        return

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
        f"{regime} x {side} x AGE {bucket}"
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

    print(
        "  Results      = "
        f"{dict(stats['results'])}"
    )


def run_audit() -> None:
    rows = load_closed_rows()

    sequence_cache: dict[
        int,
        list[dict[str, Any]],
    ] = {}

    performance = defaultdict(
        make_stats
    )

    regime_counter: Counter[str] = (
        Counter()
    )

    age_counter: Counter[
        tuple[str, str]
    ] = Counter()

    censored_counter: Counter[str] = (
        Counter()
    )

    errors: Counter[str] = Counter()

    print("=" * 96)
    print(
        "Historical Regime Transition Audit V1"
    )
    print("=" * 96)

    print(
        "Closed Shadow Records:",
        len(rows),
    )

    print(
        "Sequence Length:",
        SEQUENCE_LENGTH,
    )

    print()

    for index, row in enumerate(
        rows,
        1,
    ):
        timestamp = row["timestamp"]

        try:
            timestamp_ms = (
                timestamp_to_ms(timestamp)
            )

            bucket_ms = (
                timestamp_ms
                // INTERVAL_MS
                * INTERVAL_MS
            )

            if bucket_ms not in sequence_cache:
                sequence_cache[
                    bucket_ms
                ] = (
                    load_historical_context_sequence(
                        timestamp,
                        sequence_length=(
                            SEQUENCE_LENGTH
                        ),
                    )
                )

            sequence = sequence_cache[
                bucket_ms
            ]

            (
                regime,
                age,
                left_censored,
            ) = calculate_regime_age(
                sequence,
                classifier=classify_research_regime,
            )

            age_bucket = regime_age_bucket(
                age,
                left_censored,
            )

            side = str(
                row.get("side")
                or "UNKNOWN"
            )

            pnl = float(
                row.get("realized_pnl")
                or 0.0
            )

            result = str(
                row.get("result")
                or "UNKNOWN"
            )

            key = (
                regime,
                side,
                age_bucket,
            )

            stats = performance[key]

            stats["n"] += 1
            stats["pnl"] += pnl
            stats["results"][
                result
            ] += 1

            if pnl > 0:
                stats["wins"] += 1
                stats[
                    "gross_profit"
                ] += pnl
                stats[
                    "win_pnl"
                ] += pnl

            elif pnl < 0:
                stats["losses"] += 1
                stats[
                    "gross_loss"
                ] += pnl
                stats[
                    "loss_pnl"
                ] += pnl

            regime_counter[
                regime
            ] += 1

            age_counter[
                (
                    regime,
                    age_bucket,
                )
            ] += 1

            if left_censored:
                censored_counter[
                    regime
                ] += 1

        except Exception as exc:
            error_key = (
                f"{type(exc).__name__}: "
                f"{str(exc)[:120]}"
            )

            errors[
                error_key
            ] += 1

        if (
            index % 500 == 0
            or index == len(rows)
        ):
            print(
                f"Progress "
                f"{index}/{len(rows)}"
            )

    print()
    print("=" * 96)
    print("REGIME DISTRIBUTION")
    print("=" * 96)

    for regime in (
        "BULL",
        "BEAR",
        "RANGE",
    ):
        print(
            f"{regime:<8} "
            f"N={regime_counter[regime]}"
        )

    print()
    print("=" * 96)
    print("REGIME AGE DISTRIBUTION")
    print("=" * 96)

    for regime in (
        "BULL",
        "BEAR",
        "RANGE",
    ):
        print()
        print(regime)

        for bucket in AGE_BUCKETS:
            count = age_counter[
                (
                    regime,
                    bucket,
                )
            ]

            print(
                f"  AGE {bucket:<6} "
                f"N={count}"
            )

    print()
    print("=" * 96)
    print(
        "REGIME x DIRECTION x AGE PERFORMANCE"
    )
    print("=" * 96)

    for regime in (
        "BULL",
        "BEAR",
        "RANGE",
    ):
        for side in (
            "LONG",
            "SHORT",
        ):
            for bucket in AGE_BUCKETS:
                stats = performance[
                    (
                        regime,
                        side,
                        bucket,
                    )
                ]

                print_stats(
                    regime,
                    side,
                    bucket,
                    stats,
                )

    print()
    print("=" * 96)
    print("LEFT-CENSORED")
    print("=" * 96)

    for regime in (
        "BULL",
        "BEAR",
        "RANGE",
    ):
        print(
            f"{regime:<8} "
            f"N={censored_counter[regime]}"
        )

    print()
    print("=" * 96)
    print("CACHE / ERRORS")
    print("=" * 96)

    print(
        "Unique BTC 15m Buckets:",
        len(sequence_cache),
    )

    print(
        "Classified:",
        sum(regime_counter.values()),
    )

    print(
        "Errors:",
        sum(errors.values()),
    )

    if errors:
        print()

        for error, count in (
            errors.most_common()
        ):
            print(
                f"{count:>5} x {error}"
            )


if __name__ == "__main__":
    run_audit()
