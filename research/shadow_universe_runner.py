"""
Shadow Universe Runner V1

Research-only pipeline:

Dynamic Universe
    ->
Pre-Scanner Top N
    ->
Full LONG / SHORT AI Context
    ->
OpportunityRecord
    ->
ShadowTrade
    ->
Shadow Log

IMPORTANT:
- No exchange orders.
- No VST orders.
- Does not modify Strategy A.
- Research / observation only.
"""

from __future__ import annotations

import time

from scanner.pre_scanner import build_candidate_pool
from scanner.ai_score import (
    calculate_ai_context,
    calculate_short_ai_context,
)
from scanner.market_regime import get_market_regime
from scanner.scanner import get_regime_thresholds

from opportunity.factory import create_opportunity
from shadow.manager import create_shadow_trade
from shadow.logger import log_shadow_trade


DEFAULT_TOP_N = 100


def run_shadow_universe(
    top_n=DEFAULT_TOP_N,
):
    started = time.perf_counter()

    market_regime = get_market_regime()

    long_threshold, short_threshold = (
        get_regime_thresholds(
            market_regime
        )
    )

    print("=" * 90)
    print("Shadow Universe Runner V1")
    print("=" * 90)

    print(
        "Market Regime   :",
        market_regime,
    )
    print(
        "LONG Threshold  :",
        long_threshold,
    )
    print(
        "SHORT Threshold :",
        short_threshold,
    )
    print(
        "Top N           :",
        top_n,
    )

    print()
    print("===== PRE-SCANNER =====")

    pre_result = build_candidate_pool(
        top_n=top_n,
    )

    candidates = pre_result["candidates"]

    print()
    print(
        "Universe   :",
        pre_result["universe_count"],
    )
    print(
        "Valid      :",
        pre_result["valid_count"],
    )
    print(
        "Failed     :",
        pre_result["failed_count"],
    )
    print(
        "Candidates :",
        len(candidates),
    )

    created = []
    skipped = []
    failed = []

    print()
    print("===== FULL SHADOW ANALYSIS =====")

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):
        symbol = candidate["symbol"]

        try:
            long_context = (
                calculate_ai_context(symbol)
            )

            short_context = (
                calculate_short_ai_context(symbol)
            )

            long_score = int(
                long_context.get(
                    "score",
                    0,
                )
            )

            short_score = int(
                short_context.get(
                    "score",
                    0,
                )
            )

            can_long = (
                long_score
                >= long_threshold
            )

            can_short = (
                short_score
                >= short_threshold
            )

            opportunity = create_opportunity(
                symbol=symbol,
                market_regime=market_regime,
                long_score=long_score,
                short_score=short_score,
                long_threshold=long_threshold,
                short_threshold=short_threshold,
                can_long=can_long,
                can_short=can_short,
                reason="shadow_universe",
                context={
                    "long": long_context,
                    "short": short_context,
                },
                source="shadow_universe",
            )

            shadow_trade = (
                create_shadow_trade(
                    opportunity
                )
            )

            if shadow_trade is None:
                skipped.append(symbol)

            else:
                log_shadow_trade(
                    shadow_trade
                )

                created.append(
                    shadow_trade
                )

                print(
                    f"{symbol:20} "
                    f"{shadow_trade.side:5} "
                    f"AI={shadow_trade.ai_score:3} "
                    f"TH={shadow_trade.threshold:3} "
                    f"Entry="
                    f"{shadow_trade.entry_price}"
                )

        except Exception as exc:
            failed.append({
                "symbol": symbol,
                "error": (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            })

        if (
            index % 10 == 0
            or index == len(candidates)
        ):
            print(
                f"Progress "
                f"{index}/{len(candidates)}"
            )

    elapsed = (
        time.perf_counter()
        - started
    )

    print()
    print("=" * 90)
    print("RESULT")
    print("=" * 90)

    print(
        "Candidates     :",
        len(candidates),
    )
    print(
        "Shadow Created :",
        len(created),
    )
    print(
        "Dedup Skipped  :",
        len(skipped),
    )
    print(
        "Failed         :",
        len(failed),
    )
    print(
        "Elapsed        :",
        round(elapsed, 2),
        "seconds",
    )

    if failed:
        print()
        print("===== FAILED =====")

        for item in failed:
            print(
                item["symbol"],
                item["error"],
            )

    return {
        "market_regime": market_regime,
        "candidate_count": len(
            candidates
        ),
        "shadow_created": len(
            created
        ),
        "dedup_skipped": len(
            skipped
        ),
        "failed_count": len(
            failed
        ),
        "elapsed_seconds": round(
            elapsed,
            2,
        ),
    }


if __name__ == "__main__":
    run_shadow_universe()
