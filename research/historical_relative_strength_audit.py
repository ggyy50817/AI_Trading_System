"""
Historical Relative Strength Audit V1

Analyze Shadow performance by:

Historical BTC Regime
x Trade Side
x Altcoin-vs-BTC Relative Strength
x Momentum Window

Research only:
- No live trading
- No Strategy A modification
- No automatic parameter changes
- Historical closed-candle data only
- Strict anti-lookahead boundary
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from replay.shadow_historical_data import (
    timestamp_to_ms,
)
from research.historical_context_sequence import (
    load_historical_context_sequence,
)
from research.historical_regime_direction_diagnostic import (
    make_performance_stats,
    performance_summary,
    update_performance_stats,
)
from research.historical_regime_transition_audit import (
    classify_research_regime,
    load_closed_rows,
)
from research.historical_relative_strength import (
    close_return,
    load_historical_close_sequence,
    relative_strength,
    relative_strength_direction,
)


INTERVAL_MS = 15 * 60 * 1000

BTC_SYMBOL = "BTC-USDT"

WINDOWS = (
    (1, "15m"),
    (3, "45m"),
    (6, "90m"),
)

SEQUENCE_LENGTH = 20
REGIME_SEQUENCE_LENGTH = 80


def historical_bucket_ms(
    timestamp: str,
) -> int:
    timestamp_ms = timestamp_to_ms(
        timestamp
    )

    return (
        timestamp_ms // INTERVAL_MS
    ) * INTERVAL_MS


def get_close_sequence(
    cache: dict[
        tuple[str, int],
        list[dict[str, Any]],
    ],
    symbol: str,
    timestamp: str,
) -> list[dict[str, Any]]:

    bucket_ms = historical_bucket_ms(
        timestamp
    )

    key = (
        symbol,
        bucket_ms,
    )

    if key not in cache:
        cache[key] = (
            load_historical_close_sequence(
                symbol,
                timestamp,
                sequence_length=SEQUENCE_LENGTH,
            )
        )

    return cache[key]


def get_regime_sequence(
    cache: dict[
        int,
        list[dict[str, Any]],
    ],
    timestamp: str,
) -> list[dict[str, Any]]:

    bucket_ms = historical_bucket_ms(
        timestamp
    )

    if bucket_ms not in cache:
        cache[bucket_ms] = (
            load_historical_context_sequence(
                timestamp,
                sequence_length=(
                    REGIME_SEQUENCE_LENGTH
                ),
            )
        )

    return cache[bucket_ms]


def main() -> None:

    print("=" * 100)
    print(
        "Historical Relative Strength Audit V1"
    )
    print("=" * 100)

    rows = load_closed_rows()

    print(
        "Closed Shadow Records:",
        len(rows),
    )

    print()

    close_cache: dict[
        tuple[str, int],
        list[dict[str, Any]],
    ] = {}

    regime_cache: dict[
        int,
        list[dict[str, Any]],
    ] = {}

    stats: dict[
        int,
        dict[
            tuple[str, str, str],
            dict[str, Any],
        ],
    ] = {
        candles: {}
        for candles, _ in WINDOWS
    }

    errors = 0
    classified = 0

    for index, row in enumerate(
        rows,
        1,
    ):

        try:
            timestamp = str(
                row["timestamp"]
            )

            symbol = str(
                row["symbol"]
            ).upper()

            side = str(
                row.get("side")
            ).upper()

            pnl = float(
                row.get(
                    "realized_pnl",
                    0.0,
                )
            )

            regime_sequence = (
                get_regime_sequence(
                    regime_cache,
                    timestamp,
                )
            )

            regime = (
                classify_research_regime(
                    regime_sequence[-1]
                )
            )

            alt_sequence = (
                get_close_sequence(
                    close_cache,
                    symbol,
                    timestamp,
                )
            )

            btc_sequence = (
                get_close_sequence(
                    close_cache,
                    BTC_SYMBOL,
                    timestamp,
                )
            )

            alt_times = [
                item["candle_time_ms"]
                for item in alt_sequence
            ]

            btc_times = [
                item["candle_time_ms"]
                for item in btc_sequence
            ]

            if alt_times != btc_times:
                raise ValueError(
                    "ALT/BTC candle alignment mismatch"
                )

            for candles, _ in WINDOWS:

                alt_return = close_return(
                    alt_sequence,
                    candles,
                )

                btc_return = close_return(
                    btc_sequence,
                    candles,
                )

                rs = relative_strength(
                    alt_return,
                    btc_return,
                )

                rs_direction = (
                    relative_strength_direction(
                        rs
                    )
                )

                key = (
                    regime,
                    side,
                    rs_direction,
                )

                if key not in stats[candles]:
                    stats[candles][key] = (
                        make_performance_stats()
                    )

                update_performance_stats(
                    stats[candles][key],
                    pnl,
                )

            classified += 1

        except Exception as exc:
            errors += 1

            if errors <= 10:
                print(
                    "ERROR:",
                    row.get("timestamp"),
                    row.get("symbol"),
                    repr(exc),
                )

        if (
            index % 500 == 0
            or index == len(rows)
        ):
            print(
                f"Progress "
                f"{index}/{len(rows)}"
            )

    for candles, label in WINDOWS:

        print()
        print("=" * 100)
        print(
            f"RELATIVE STRENGTH WINDOW = {label}"
        )
        print("=" * 100)

        keys = sorted(
            stats[candles].keys()
        )

        for key in keys:

            (
                regime,
                side,
                rs_direction,
            ) = key

            summary = performance_summary(
                stats[candles][key]
            )

            pf = summary[
                "profit_factor"
            ]

            if isinstance(pf, float):
                pf_text = f"{pf:.3f}"
            else:
                pf_text = str(pf)

            print(
                f"{regime:<5} x "
                f"{side:<5} x "
                f"{rs_direction:<12} | "
                f"N={summary['n']:>4} | "
                f"WR={summary['win_rate']:>6.2f}% | "
                f"PNL={summary['pnl']:>10.4f} | "
                f"EXP={summary['expectancy']:>8.4f} | "
                f"PF={pf_text}"
            )

    print()
    print("=" * 100)
    print("CACHE / ERRORS")
    print("=" * 100)

    print(
        "CLOSE CACHE ENTRIES =",
        len(close_cache),
    )

    print(
        "REGIME CACHE ENTRIES =",
        len(regime_cache),
    )

    print(
        "CLASSIFIED =",
        classified,
    )

    print(
        "ERRORS =",
        errors,
    )

    print("=" * 100)


if __name__ == "__main__":
    main()
