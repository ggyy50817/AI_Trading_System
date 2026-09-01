"""
Historical BEAR Slope Threshold Sensitivity Audit V1

Research only.

Purpose:
- Hold Raw BEAR structure, ATR gate, and Volume gate constant.
- Vary only the normalized MA20 slope magnitude threshold.
- Measure whether stricter slope confirmation produces:
    1. fewer available Raw BEAR episodes,
    2. longer confirmation lag,
    3. larger price decline before confirmation,
    4. more positive / rebound-biased forward returns.

This is a mechanism / sensitivity audit, NOT an optimizer.

No live trading.
No Strategy A modification.
No automatic parameter changes.
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from replay.shadow_historical_data import fetch_klines_range
from research.historical_context_sequence import (
    build_context_sequence_from_dataframe,
)
from research.historical_bear_gate_lag_attribution_audit import (
    gate_flags,
    group_raw_bear_episodes,
)
from research.historical_bear_gate_counterfactual_forward_return_audit import (
    build_close_map,
    calculate_forward_returns,
)


SYMBOL = "BTC-USDT"
INTERVAL = "15m"

START_DT = datetime(
    2026, 6, 1,
    tzinfo=timezone.utc,
)

END_DT = datetime(
    2026, 8, 21,
    tzinfo=timezone.utc,
)

INTERVAL_MS = 15 * 60 * 1000

# Pre-registered research grid.
# Do not change after seeing results in this V1 audit.
SLOPE_THRESHOLDS = (
    0.00025,
    0.00050,
    0.00075,
    0.00100,
    0.00125,
)

FORWARD_LABELS = (
    "15m",
    "45m",
    "90m",
    "3h",
)


def percentile(
    values: list[float],
    q: float,
) -> float:
    if not values:
        return float("nan")

    return float(
        np.percentile(
            np.asarray(
                values,
                dtype=float,
            ),
            q,
        )
    )


def summarize(
    values: list[float],
) -> dict[str, float]:
    if not values:
        return {
            "count": 0,
            "average": float("nan"),
            "median": float("nan"),
            "p25": float("nan"),
            "p75": float("nan"),
            "minimum": float("nan"),
            "maximum": float("nan"),
            "positive": 0,
            "negative": 0,
            "zero": 0,
            "positive_rate": float("nan"),
            "negative_rate": float("nan"),
        }

    array = np.asarray(
        values,
        dtype=float,
    )

    positive = int(
        np.sum(array > 0)
    )

    negative = int(
        np.sum(array < 0)
    )

    zero = int(
        np.sum(array == 0)
    )

    count = len(values)

    return {
        "count": count,
        "average": float(
            np.mean(array)
        ),
        "median": float(
            np.median(array)
        ),
        "p25": percentile(
            values,
            25,
        ),
        "p75": percentile(
            values,
            75,
        ),
        "minimum": float(
            np.min(array)
        ),
        "maximum": float(
            np.max(array)
        ),
        "positive": positive,
        "negative": negative,
        "zero": zero,
        "positive_rate": (
            positive / count * 100.0
        ),
        "negative_rate": (
            negative / count * 100.0
        ),
    }


def normalized_slope(
    context: dict,
) -> float:
    close = float(
        context["latest_close"]
    )

    slope = float(
        context["ma20_slope"]
    )

    if close <= 0:
        return float("nan")

    return abs(slope) / close


def threshold_pass(
    context: dict,
    threshold: float,
) -> bool:
    """
    Counterfactual Production BEAR condition.

    Raw BEAR episode membership is already guaranteed
    by group_raw_bear_episodes().

    ATR and Volume retain their existing gate logic.
    Only slope threshold changes.
    """
    flags = gate_flags(context)

    return (
        flags["atr_pass"]
        and flags["volume_pass"]
        and normalized_slope(context)
        >= threshold
    )


def find_first_threshold_context(
    episode: list[dict],
    threshold: float,
) -> dict | None:
    for context in episode:
        if threshold_pass(
            context,
            threshold,
        ):
            return context

    return None


def build_threshold_records(
    episodes: list[list[dict]],
    threshold: float,
    close_map: dict[int, float],
) -> list[dict]:
    records: list[dict] = []

    for episode in episodes:
        if not episode:
            continue

        raw_start = episode[0]

        selected = (
            find_first_threshold_context(
                episode,
                threshold,
            )
        )

        if selected is None:
            continue

        raw_time_ms = int(
            raw_start["candle_time_ms"]
        )

        selected_time_ms = int(
            selected["candle_time_ms"]
        )

        lag_delta = (
            selected_time_ms
            - raw_time_ms
        )

        if lag_delta < 0:
            raise AssertionError(
                "Negative threshold lag"
            )

        if (
            lag_delta
            % INTERVAL_MS
            != 0
        ):
            raise AssertionError(
                "Threshold lag is not aligned "
                "to 15m bars"
            )

        lag_bars = int(
            lag_delta
            // INTERVAL_MS
        )

        raw_close = float(
            raw_start["latest_close"]
        )

        selected_close = float(
            selected["latest_close"]
        )

        price_move = (
            (
                selected_close
                / raw_close
            )
            - 1.0
        ) * 100.0

        forward = (
            calculate_forward_returns(
                selected,
                close_map,
            )
        )

        if forward is None:
            continue

        record = {
            "raw_time_ms": raw_time_ms,
            "selected_time_ms": (
                selected_time_ms
            ),
            "lag_bars": lag_bars,
            "lag_minutes": (
                lag_bars * 15
            ),
            "price_move": price_move,
            "normalized_slope": (
                normalized_slope(
                    selected
                )
            ),
            "volume_ratio": float(
                selected[
                    "volume_ratio"
                ]
            ),
        }

        for label in FORWARD_LABELS:
            record[
                f"return_{label}"
            ] = float(
                forward[label]
            )

        records.append(record)

    return records


def summarize_threshold(
    records: list[dict],
) -> dict:
    lag_bars = [
        float(
            record["lag_bars"]
        )
        for record in records
    ]

    lag_minutes = [
        float(
            record["lag_minutes"]
        )
        for record in records
    ]

    price_moves = [
        float(
            record["price_move"]
        )
        for record in records
    ]

    normalized_slopes = [
        float(
            record[
                "normalized_slope"
            ]
        )
        for record in records
    ]

    result = {
        "count": len(records),
        "lag_bars": summarize(
            lag_bars
        ),
        "lag_minutes": summarize(
            lag_minutes
        ),
        "price_move": summarize(
            price_moves
        ),
        "normalized_slope": summarize(
            normalized_slopes
        ),
        "forward": {},
    }

    for label in FORWARD_LABELS:
        values = [
            float(
                record[
                    f"return_{label}"
                ]
            )
            for record in records
        ]

        result["forward"][label] = (
            summarize(values)
        )

    return result


def print_threshold_summary(
    threshold: float,
    summary: dict,
    raw_episode_count: int,
) -> None:
    print()
    print(
        f"--- SLOPE THRESHOLD "
        f"{threshold:.5f} "
        f"({threshold * 100:.3f}%) ---"
    )

    count = int(
        summary["count"]
    )

    availability = (
        count
        / raw_episode_count
        * 100.0
        if raw_episode_count
        else float("nan")
    )

    print(
        f"AVAILABLE EPISODES           : "
        f"{count}"
    )

    print(
        f"EPISODE AVAILABILITY         : "
        f"{availability:.2f}%"
    )

    print(
        f"LAG BARS AVG                 : "
        f"{summary['lag_bars']['average']:.3f}"
    )

    print(
        f"LAG BARS MEDIAN              : "
        f"{summary['lag_bars']['median']:.3f}"
    )

    print(
        f"LAG MINUTES AVG              : "
        f"{summary['lag_minutes']['average']:.2f}"
    )

    print(
        f"LAG MINUTES MEDIAN           : "
        f"{summary['lag_minutes']['median']:.2f}"
    )

    print(
        f"PRICE MOVE AVG               : "
        f"{summary['price_move']['average']:+.6f}%"
    )

    print(
        f"PRICE MOVE MEDIAN            : "
        f"{summary['price_move']['median']:+.6f}%"
    )

    print(
        f"CONFIRM |SLOPE|/CLOSE AVG    : "
        f"{summary['normalized_slope']['average'] * 100:.6f}%"
    )

    print(
        f"CONFIRM |SLOPE|/CLOSE MEDIAN : "
        f"{summary['normalized_slope']['median'] * 100:.6f}%"
    )

    for label in FORWARD_LABELS:
        forward = (
            summary["forward"][label]
        )

        print(
            f"{label:<6} "
            f"N={int(forward['count']):3d}  "
            f"AVG={forward['average']:+.6f}%  "
            f"MED={forward['median']:+.6f}%  "
            f"UP={forward['positive_rate']:6.2f}%  "
            f"DOWN={forward['negative_rate']:6.2f}%"
        )


def print_compact_table(
    results: dict[float, dict],
) -> None:
    print()
    print(
        "=" * 110
    )

    print(
        "COMPACT DOSE-RESPONSE TABLE"
    )

    print(
        "=" * 110
    )

    print(
        "THRESHOLD   N    "
        "LAG_MED   MOVE_MED     "
        "3H_AVG       3H_MED       "
        "3H_UP"
    )

    for threshold in SLOPE_THRESHOLDS:
        summary = results[
            threshold
        ]

        forward_3h = (
            summary["forward"]["3h"]
        )

        print(
            f"{threshold:0.5f}   "
            f"{summary['count']:3d}   "
            f"{summary['lag_bars']['median']:7.2f}   "
            f"{summary['price_move']['median']:+10.6f}%   "
            f"{forward_3h['average']:+10.6f}%   "
            f"{forward_3h['median']:+10.6f}%   "
            f"{forward_3h['positive_rate']:6.2f}%"
        )


def run_audit() -> None:
    start_ms = int(
        START_DT.timestamp()
        * 1000
    )

    end_ms = int(
        END_DT.timestamp()
        * 1000
    )

    df = fetch_klines_range(
        SYMBOL,
        start_ms,
        end_ms,
        interval=INTERVAL,
    )

    contexts = (
        build_context_sequence_from_dataframe(
            df
        )
    )

    raw_episodes = (
        group_raw_bear_episodes(
            contexts
        )
    )

    close_map = build_close_map(
        df
    )

    print(
        "=" * 110
    )

    print(
        "HISTORICAL BEAR SLOPE "
        "THRESHOLD SENSITIVITY AUDIT V1"
    )

    print(
        "=" * 110
    )

    print()
    print(
        f"KLINES                       : "
        f"{len(df)}"
    )

    print(
        f"MATURE CONTEXTS              : "
        f"{len(contexts)}"
    )

    print(
        f"RAW BEAR EPISODES            : "
        f"{len(raw_episodes)}"
    )

    print(
        "THRESHOLD GRID               : "
        + ", ".join(
            f"{value:.5f}"
            for value
            in SLOPE_THRESHOLDS
        )
    )

    print()
    print(
        "=" * 110
    )

    print(
        "1. THRESHOLD SENSITIVITY"
    )

    print(
        "=" * 110
    )

    results: dict[
        float,
        dict,
    ] = {}

    records_by_threshold: dict[
        float,
        list[dict],
    ] = {}

    for threshold in (
        SLOPE_THRESHOLDS
    ):
        records = (
            build_threshold_records(
                raw_episodes,
                threshold,
                close_map,
            )
        )

        records_by_threshold[
            threshold
        ] = records

        summary = (
            summarize_threshold(
                records
            )
        )

        results[
            threshold
        ] = summary

        print_threshold_summary(
            threshold,
            summary,
            len(raw_episodes),
        )

    print_compact_table(
        results
    )

    print()
    print(
        "=" * 110
    )

    print(
        "2. PRODUCTION THRESHOLD "
        "REFERENCE"
    )

    print(
        "=" * 110
    )

    production_threshold = (
        0.00100
    )

    production = results[
        production_threshold
    ]

    print(
        f"PRODUCTION THRESHOLD         : "
        f"{production_threshold:.5f}"
    )

    print(
        f"AVAILABLE EPISODES           : "
        f"{production['count']}"
    )

    print(
        f"LAG BARS AVG                 : "
        f"{production['lag_bars']['average']:.3f}"
    )

    print(
        f"LAG BARS MEDIAN              : "
        f"{production['lag_bars']['median']:.3f}"
    )

    print(
        f"PRICE MOVE AVG               : "
        f"{production['price_move']['average']:+.6f}%"
    )

    print(
        f"PRICE MOVE MEDIAN            : "
        f"{production['price_move']['median']:+.6f}%"
    )

    print(
        f"POST 3H AVG                  : "
        f"{production['forward']['3h']['average']:+.6f}%"
    )

    print(
        f"POST 3H MEDIAN               : "
        f"{production['forward']['3h']['median']:+.6f}%"
    )

    print(
        f"POST 3H UP                   : "
        f"{production['forward']['3h']['positive_rate']:.2f}%"
    )

    print()
    print(
        "=" * 110
    )

    print(
        "3. FINAL CHECK"
    )

    print(
        "=" * 110
    )

    raw_episode_check = (
        len(raw_episodes)
        == 276
    )

    threshold_grid_check = (
        SLOPE_THRESHOLDS
        == (
            0.00025,
            0.00050,
            0.00075,
            0.00100,
            0.00125,
        )
    )

    availability_monotonic = all(
        results[
            SLOPE_THRESHOLDS[i]
        ]["count"]
        >= results[
            SLOPE_THRESHOLDS[
                i + 1
            ]
        ]["count"]
        for i in range(
            len(
                SLOPE_THRESHOLDS
            )
            - 1
        )
    )

    production_count_check = (
        production["count"]
        == 21
    )

    threshold_pass_check = True

    for threshold in (
        SLOPE_THRESHOLDS
    ):
        for record in (
            records_by_threshold[
                threshold
            ]
        ):
            if (
                record[
                    "normalized_slope"
                ]
                + 1e-15
                < threshold
            ):
                threshold_pass_check = (
                    False
                )

    nonnegative_lag_check = all(
        record["lag_bars"] >= 0
        for threshold in (
            SLOPE_THRESHOLDS
        )
        for record in (
            records_by_threshold[
                threshold
            ]
        )
    )

    overall_check = all(
        (
            raw_episode_check,
            threshold_grid_check,
            availability_monotonic,
            production_count_check,
            threshold_pass_check,
            nonnegative_lag_check,
        )
    )

    checks = (
        (
            "RAW EPISODE CHECK",
            raw_episode_check,
        ),
        (
            "THRESHOLD GRID CHECK",
            threshold_grid_check,
        ),
        (
            "AVAILABILITY MONOTONIC CHECK",
            availability_monotonic,
        ),
        (
            "PRODUCTION COUNT CHECK",
            production_count_check,
        ),
        (
            "THRESHOLD PASS CHECK",
            threshold_pass_check,
        ),
        (
            "NONNEGATIVE LAG CHECK",
            nonnegative_lag_check,
        ),
        (
            "OVERALL CHECK",
            overall_check,
        ),
    )

    for name, passed in checks:
        print(
            f"{name:<30}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    print(
        "=" * 110
    )


if __name__ == "__main__":
    run_audit()
