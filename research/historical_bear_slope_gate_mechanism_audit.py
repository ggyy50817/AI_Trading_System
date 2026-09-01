"""
Historical BEAR Slope Gate Mechanism Audit V1

Purpose:
- Inspect the mechanism between Raw BEAR onset and first Production BEAR.
- Focus on Raw BEAR episodes that eventually reach Production.
- Measure:
    * MA20 slope direction
    * normalized slope magnitude
    * distance to production slope threshold
    * volume status
    * price movement
    * confirmation lag

Research only:
- No Strategy A modification
- No production threshold modification
- No automatic parameter changes
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from replay.shadow_historical_data import fetch_klines_range
from research.historical_context_sequence import (
    build_context_sequence_from_dataframe,
)
from research.historical_regime_gate_distribution_audit import (
    SLOPE_THRESHOLD,
    VOLUME_THRESHOLD,
)
from research.historical_bear_gate_lag_attribution_audit import (
    classify_bear_paths,
    group_raw_bear_episodes,
    find_first_path_context,
)


START = datetime(2026, 6, 1, tzinfo=timezone.utc)
END = datetime(2026, 8, 21, tzinfo=timezone.utc)

INTERVAL_MS = 15 * 60 * 1000


def slope_metrics(context):
    close = float(
        context["latest_close"]
    )

    slope = float(
        context["ma20_slope"]
    )

    volume_ratio = float(
        context["volume_ratio"]
    )

    normalized_signed = (
        slope / close
        if close != 0
        else 0.0
    )

    normalized_abs = abs(
        normalized_signed
    )

    threshold_ratio = (
        normalized_abs
        / SLOPE_THRESHOLD
        if SLOPE_THRESHOLD != 0
        else float("inf")
    )

    threshold_gap = (
        normalized_abs
        - SLOPE_THRESHOLD
    )

    return {
        "close": close,
        "slope": slope,
        "normalized_signed": normalized_signed,
        "normalized_abs": normalized_abs,
        "threshold_ratio": threshold_ratio,
        "threshold_gap": threshold_gap,
        "slope_pass": (
            normalized_abs
            >= SLOPE_THRESHOLD
        ),
        "volume_ratio": volume_ratio,
        "volume_pass": (
            volume_ratio
            >= VOLUME_THRESHOLD
        ),
    }


def summarize(values):
    if not values:
        return None

    array = np.asarray(
        values,
        dtype=float,
    )

    return {
        "n": len(array),
        "average": float(
            np.mean(array)
        ),
        "median": float(
            np.percentile(array, 50)
        ),
        "p25": float(
            np.percentile(array, 25)
        ),
        "p75": float(
            np.percentile(array, 75)
        ),
        "minimum": float(
            np.min(array)
        ),
        "maximum": float(
            np.max(array)
        ),
    }


def sign_name(value):
    if value > 0:
        return "POS"

    if value < 0:
        return "NEG"

    return "ZERO"


def build_matched_records(episodes):
    records = []

    for episode in episodes:
        production_context = (
            find_first_path_context(
                episode,
                "PRODUCTION",
            )
        )

        if production_context is None:
            continue

        raw_context = episode[0]

        volume_context = (
            find_first_path_context(
                episode,
                "RAW+ATR+VOLUME",
            )
        )

        if volume_context is None:
            raise RuntimeError(
                "Production exists without "
                "RAW+ATR+VOLUME path."
            )

        raw_ms = int(
            raw_context["candle_time_ms"]
        )

        production_ms = int(
            production_context[
                "candle_time_ms"
            ]
        )

        production_index = None

        for index, context in enumerate(
            episode
        ):
            if (
                int(context["candle_time_ms"])
                == production_ms
            ):
                production_index = index
                break

        if production_index is None:
            raise RuntimeError(
                "Production context not found "
                "inside Raw BEAR episode."
            )

        path_contexts = episode[
            : production_index + 1
        ]

        raw_metrics = slope_metrics(
            raw_context
        )

        volume_metrics = slope_metrics(
            volume_context
        )

        production_metrics = slope_metrics(
            production_context
        )

        raw_close = raw_metrics["close"]
        production_close = (
            production_metrics["close"]
        )

        price_move_pct = (
            production_close
            / raw_close
            - 1.0
        ) * 100.0

        lag_bars = (
            production_ms - raw_ms
        ) // INTERVAL_MS

        path_metrics = [
            slope_metrics(context)
            for context in path_contexts
        ]

        negative_slope_bars = sum(
            1
            for metrics in path_metrics
            if metrics[
                "normalized_signed"
            ] < 0
        )

        positive_slope_bars = sum(
            1
            for metrics in path_metrics
            if metrics[
                "normalized_signed"
            ] > 0
        )

        slope_pass_bars = sum(
            1
            for metrics in path_metrics
            if metrics["slope_pass"]
        )

        volume_pass_bars = sum(
            1
            for metrics in path_metrics
            if metrics["volume_pass"]
        )

        records.append(
            {
                "raw_context": raw_context,
                "volume_context": volume_context,
                "production_context": (
                    production_context
                ),
                "raw_metrics": raw_metrics,
                "volume_metrics": (
                    volume_metrics
                ),
                "production_metrics": (
                    production_metrics
                ),
                "path_metrics": path_metrics,
                "path_bars": len(
                    path_metrics
                ),
                "lag_bars": int(
                    lag_bars
                ),
                "price_move_pct": float(
                    price_move_pct
                ),
                "negative_slope_bars": (
                    negative_slope_bars
                ),
                "positive_slope_bars": (
                    positive_slope_bars
                ),
                "slope_pass_bars": (
                    slope_pass_bars
                ),
                "volume_pass_bars": (
                    volume_pass_bars
                ),
            }
        )

    return records


def print_stage_summary(
    name,
    records,
    metrics_key,
):
    signed = [
        record[metrics_key][
            "normalized_signed"
        ] * 100.0
        for record in records
    ]

    magnitude = [
        record[metrics_key][
            "normalized_abs"
        ] * 100.0
        for record in records
    ]

    threshold_ratio = [
        record[metrics_key][
            "threshold_ratio"
        ]
        for record in records
    ]

    volume_ratio = [
        record[metrics_key][
            "volume_ratio"
        ]
        for record in records
    ]

    signed_stats = summarize(signed)
    magnitude_stats = summarize(
        magnitude
    )
    threshold_stats = summarize(
        threshold_ratio
    )
    volume_stats = summarize(
        volume_ratio
    )

    positive = sum(
        1
        for value in signed
        if value > 0
    )

    negative = sum(
        1
        for value in signed
        if value < 0
    )

    slope_pass = sum(
        1
        for record in records
        if record[metrics_key][
            "slope_pass"
        ]
    )

    volume_pass = sum(
        1
        for record in records
        if record[metrics_key][
            "volume_pass"
        ]
    )

    n = len(records)

    print()
    print(f"--- {name} ---")
    print(
        f"N                            : "
        f"{n}"
    )
    print(
        f"SLOPE POSITIVE               : "
        f"{positive} "
        f"({positive / n * 100:.2f}%)"
    )
    print(
        f"SLOPE NEGATIVE               : "
        f"{negative} "
        f"({negative / n * 100:.2f}%)"
    )
    print(
        f"SIGNED SLOPE/CLOSE AVG       : "
        f"{signed_stats['average']:+.6f}%"
    )
    print(
        f"SIGNED SLOPE/CLOSE MEDIAN    : "
        f"{signed_stats['median']:+.6f}%"
    )
    print(
        f"|SLOPE|/CLOSE AVG            : "
        f"{magnitude_stats['average']:.6f}%"
    )
    print(
        f"|SLOPE|/CLOSE MEDIAN         : "
        f"{magnitude_stats['median']:.6f}%"
    )
    print(
        f"THRESHOLD RATIO AVG          : "
        f"{threshold_stats['average']:.4f}x"
    )
    print(
        f"THRESHOLD RATIO MEDIAN       : "
        f"{threshold_stats['median']:.4f}x"
    )
    print(
        f"SLOPE PASS                   : "
        f"{slope_pass} "
        f"({slope_pass / n * 100:.2f}%)"
    )
    print(
        f"VOLUME RATIO AVG             : "
        f"{volume_stats['average']:.4f}"
    )
    print(
        f"VOLUME RATIO MEDIAN          : "
        f"{volume_stats['median']:.4f}"
    )
    print(
        f"VOLUME PASS                  : "
        f"{volume_pass} "
        f"({volume_pass / n * 100:.2f}%)"
    )


def run_audit():
    start_ms = int(
        START.timestamp() * 1000
    )

    end_ms = int(
        END.timestamp() * 1000
    )

    print("=" * 110)
    print(
        "HISTORICAL BEAR SLOPE GATE "
        "MECHANISM AUDIT V1"
    )
    print("=" * 110)

    df = fetch_klines_range(
        "BTC-USDT",
        start_ms,
        end_ms,
        interval="15m",
        page_limit=500,
    )

    contexts = (
        build_context_sequence_from_dataframe(
            df
        )
    )

    episodes = group_raw_bear_episodes(
        contexts
    )

    records = build_matched_records(
        episodes
    )

    print()
    print("KLINES                       :", len(df))
    print("MATURE CONTEXTS              :", len(contexts))
    print("RAW BEAR EPISODES            :", len(episodes))
    print(
        "MATCHED PRODUCTION EPISODES  :",
        len(records),
    )
    print(
        "SLOPE THRESHOLD              :",
        f"{SLOPE_THRESHOLD:.6f}",
    )
    print(
        "SLOPE THRESHOLD % OF CLOSE   :",
        f"{SLOPE_THRESHOLD * 100:.4f}%",
    )

    print()
    print("=" * 110)
    print("1. STAGE MECHANISM SUMMARY")
    print("=" * 110)

    print_stage_summary(
        "RAW BEAR START",
        records,
        "raw_metrics",
    )

    print_stage_summary(
        "FIRST VOLUME-QUALIFIED BEAR",
        records,
        "volume_metrics",
    )

    print_stage_summary(
        "FIRST PRODUCTION BEAR",
        records,
        "production_metrics",
    )

    print()
    print("=" * 110)
    print("2. RAW -> PRODUCTION CHANGE")
    print("=" * 110)

    lag_values = [
        record["lag_bars"]
        for record in records
    ]

    price_moves = [
        record["price_move_pct"]
        for record in records
    ]

    raw_magnitudes = [
        record["raw_metrics"][
            "normalized_abs"
        ] * 100.0
        for record in records
    ]

    production_magnitudes = [
        record["production_metrics"][
            "normalized_abs"
        ] * 100.0
        for record in records
    ]

    magnitude_changes = [
        production - raw
        for raw, production in zip(
            raw_magnitudes,
            production_magnitudes,
        )
    ]

    lag_stats = summarize(
        lag_values
    )

    price_stats = summarize(
        price_moves
    )

    magnitude_change_stats = (
        summarize(
            magnitude_changes
        )
    )

    print(
        f"LAG BARS AVG                 : "
        f"{lag_stats['average']:.3f}"
    )
    print(
        f"LAG BARS MEDIAN              : "
        f"{lag_stats['median']:.3f}"
    )
    print(
        f"LAG MINUTES AVG              : "
        f"{lag_stats['average'] * 15:.2f}"
    )
    print(
        f"LAG MINUTES MEDIAN           : "
        f"{lag_stats['median'] * 15:.2f}"
    )
    print(
        f"PRICE MOVE AVG               : "
        f"{price_stats['average']:+.6f}%"
    )
    print(
        f"PRICE MOVE MEDIAN            : "
        f"{price_stats['median']:+.6f}%"
    )
    print(
        f"|SLOPE|/CLOSE CHANGE AVG     : "
        f"{magnitude_change_stats['average']:+.6f}%"
    )
    print(
        f"|SLOPE|/CLOSE CHANGE MEDIAN  : "
        f"{magnitude_change_stats['median']:+.6f}%"
    )

    magnitude_increased = sum(
        1
        for change in magnitude_changes
        if change > 0
    )

    magnitude_decreased = sum(
        1
        for change in magnitude_changes
        if change < 0
    )

    print(
        f"SLOPE MAGNITUDE INCREASED    : "
        f"{magnitude_increased} "
        f"({magnitude_increased / len(records) * 100:.2f}%)"
    )
    print(
        f"SLOPE MAGNITUDE DECREASED    : "
        f"{magnitude_decreased} "
        f"({magnitude_decreased / len(records) * 100:.2f}%)"
    )

    print()
    print("=" * 110)
    print("3. PATH DIRECTION / GATE BEHAVIOR")
    print("=" * 110)

    total_path_bars = sum(
        record["path_bars"]
        for record in records
    )

    negative_path_bars = sum(
        record["negative_slope_bars"]
        for record in records
    )

    positive_path_bars = sum(
        record["positive_slope_bars"]
        for record in records
    )

    slope_pass_path_bars = sum(
        record["slope_pass_bars"]
        for record in records
    )

    volume_pass_path_bars = sum(
        record["volume_pass_bars"]
        for record in records
    )

    print(
        f"TOTAL RAW->PROD PATH BARS    : "
        f"{total_path_bars}"
    )
    print(
        f"NEGATIVE SLOPE BARS          : "
        f"{negative_path_bars} "
        f"({negative_path_bars / total_path_bars * 100:.2f}%)"
    )
    print(
        f"POSITIVE SLOPE BARS          : "
        f"{positive_path_bars} "
        f"({positive_path_bars / total_path_bars * 100:.2f}%)"
    )
    print(
        f"SLOPE-PASS BARS              : "
        f"{slope_pass_path_bars} "
        f"({slope_pass_path_bars / total_path_bars * 100:.2f}%)"
    )
    print(
        f"VOLUME-PASS BARS             : "
        f"{volume_pass_path_bars} "
        f"({volume_pass_path_bars / total_path_bars * 100:.2f}%)"
    )

    print()
    print("=" * 110)
    print("4. MATCHED EPISODE DETAILS")
    print("=" * 110)

    for index, record in enumerate(
        records,
        start=1,
    ):
        raw_context = record[
            "raw_context"
        ]

        raw_dt = datetime.fromtimestamp(
            int(
                raw_context[
                    "candle_time_ms"
                ]
            ) / 1000,
            tz=timezone.utc,
        )

        raw = record["raw_metrics"]
        volume = record[
            "volume_metrics"
        ]
        production = record[
            "production_metrics"
        ]

        print(
            f"{index:03d}  "
            f"{raw_dt.isoformat()}  "
            f"LAG={record['lag_bars']:2d}  "
            f"MOVE={record['price_move_pct']:+.6f}%  "
            f"RAW_S={raw['normalized_signed'] * 100:+.6f}%  "
            f"VOL_S={volume['normalized_signed'] * 100:+.6f}%  "
            f"PROD_S={production['normalized_signed'] * 100:+.6f}%  "
            f"PROD_SIGN={sign_name(production['normalized_signed'])}  "
            f"RAW_V={raw['volume_ratio']:.3f}  "
            f"VOL_V={volume['volume_ratio']:.3f}  "
            f"PROD_V={production['volume_ratio']:.3f}"
        )

    print()
    print("=" * 110)
    print("5. FINAL CHECK")
    print("=" * 110)

    raw_episode_check = (
        len(episodes) == 276
    )

    matched_check = (
        len(records) == 21
    )

    production_pass_check = all(
        classify_bear_paths(
            record[
                "production_context"
            ]
        )["PRODUCTION"]
        for record in records
    )

    slope_pass_check = all(
        record[
            "production_metrics"
        ]["slope_pass"]
        for record in records
    )

    volume_pass_check = all(
        record[
            "production_metrics"
        ]["volume_pass"]
        for record in records
    )

    lag_nonnegative_check = all(
        record["lag_bars"] >= 0
        for record in records
    )

    print(
        "RAW EPISODE CHECK            :",
        "PASS"
        if raw_episode_check
        else "FAIL",
    )
    print(
        "MATCHED EPISODE CHECK        :",
        "PASS"
        if matched_check
        else "FAIL",
    )
    print(
        "PRODUCTION PATH CHECK        :",
        "PASS"
        if production_pass_check
        else "FAIL",
    )
    print(
        "PRODUCTION SLOPE CHECK       :",
        "PASS"
        if slope_pass_check
        else "FAIL",
    )
    print(
        "PRODUCTION VOLUME CHECK      :",
        "PASS"
        if volume_pass_check
        else "FAIL",
    )
    print(
        "NONNEGATIVE LAG CHECK        :",
        "PASS"
        if lag_nonnegative_check
        else "FAIL",
    )

    overall_check = (
        raw_episode_check
        and matched_check
        and production_pass_check
        and slope_pass_check
        and volume_pass_check
        and lag_nonnegative_check
    )

    print(
        "OVERALL CHECK                :",
        "PASS"
        if overall_check
        else "FAIL",
    )

    print("=" * 110)


if __name__ == "__main__":
    run_audit()
