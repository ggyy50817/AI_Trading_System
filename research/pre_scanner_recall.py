import time

from scanner.ai_score import (
    calculate_ai_context,
    calculate_short_ai_context,
)
from scanner.market_regime import get_market_regime
from scanner.pre_scanner import build_candidate_pool
from scanner.scanner import get_regime_thresholds
from scanner.universe import build_dynamic_universe


TOP_N = 100


def run_recall_test(top_n=TOP_N):
    symbols = build_dynamic_universe()

    regime = get_market_regime()
    long_threshold, short_threshold = (
        get_regime_thresholds(regime)
    )

    print("=" * 90)
    print("Pre-Scanner Recall Test V1")
    print("=" * 90)

    print("Market Regime   :", regime)
    print("LONG Threshold  :", long_threshold)
    print("SHORT Threshold :", short_threshold)
    print("Universe        :", len(symbols))
    print("Top N           :", top_n)
    print()

    print("===== PRE-SCANNER =====")

    pre = build_candidate_pool(
        symbols=symbols,
        top_n=top_n,
    )

    candidate_symbols = {
        item["symbol"]
        for item in pre["candidates"]
    }

    rank_map = {
        item["symbol"]: index
        for index, item in enumerate(
            pre["candidates"],
            start=1,
        )
    }

    print()
    print(
        f"Pre-Scanner elapsed: "
        f"{pre['elapsed_seconds']} sec"
    )

    print()
    print("===== FULL STRATEGY A =====")

    started = time.perf_counter()

    full_candidates = []
    failed = []

    for index, symbol in enumerate(
        symbols,
        start=1,
    ):
        try:
            long_context = calculate_ai_context(
                symbol
            )
            short_context = (
                calculate_short_ai_context(
                    symbol
                )
            )

            long_score = int(
                long_context.get("score", 0)
            )
            short_score = int(
                short_context.get("score", 0)
            )

            if long_score >= long_threshold:
                full_candidates.append({
                    "symbol": symbol,
                    "side": "LONG",
                    "score": long_score,
                    "captured": (
                        symbol
                        in candidate_symbols
                    ),
                    "rank": rank_map.get(
                        symbol
                    ),
                })

            if short_score >= short_threshold:
                full_candidates.append({
                    "symbol": symbol,
                    "side": "SHORT",
                    "score": short_score,
                    "captured": (
                        symbol
                        in candidate_symbols
                    ),
                    "rank": rank_map.get(
                        symbol
                    ),
                })

        except Exception as exc:
            failed.append({
                "symbol": symbol,
                "error": (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            })

        if (
            index % 50 == 0
            or index == len(symbols)
        ):
            print(
                f"Progress "
                f"{index}/{len(symbols)}"
            )

    full_elapsed = (
        time.perf_counter() - started
    )

    long_rows = [
        row for row in full_candidates
        if row["side"] == "LONG"
    ]

    short_rows = [
        row for row in full_candidates
        if row["side"] == "SHORT"
    ]

    def recall(rows):
        if not rows:
            return 100.0

        captured = sum(
            1
            for row in rows
            if row["captured"]
        )

        return (
            captured / len(rows) * 100
        )

    captured_all = [
        row for row in full_candidates
        if row["captured"]
    ]

    missed = [
        row for row in full_candidates
        if not row["captured"]
    ]

    print()
    print("=" * 90)
    print("RESULT")
    print("=" * 90)

    print(
        f"Full Scan elapsed : "
        f"{full_elapsed:.2f} sec"
    )
    print(
        f"Full Candidates   : "
        f"{len(full_candidates)}"
    )
    print(
        f"Captured          : "
        f"{len(captured_all)}"
    )
    print(
        f"Missed            : "
        f"{len(missed)}"
    )

    overall_recall = (
        len(captured_all)
        / len(full_candidates)
        * 100
        if full_candidates
        else 100.0
    )

    print(
        f"Overall Recall    : "
        f"{overall_recall:.2f}%"
    )

    print()
    print(
        f"LONG Candidates   : "
        f"{len(long_rows)}"
    )
    print(
        f"LONG Recall       : "
        f"{recall(long_rows):.2f}%"
    )

    print()
    print(
        f"SHORT Candidates  : "
        f"{len(short_rows)}"
    )
    print(
        f"SHORT Recall      : "
        f"{recall(short_rows):.2f}%"
    )

    print()
    print("===== FULL CANDIDATES =====")

    for row in full_candidates:
        print(
            f"{row['side']:5} "
            f"{row['symbol']:20} "
            f"AI={row['score']:3} "
            f"CAPTURED="
            f"{row['captured']} "
            f"RANK={row['rank']}"
        )

    print()
    print("===== MISSED =====")

    if not missed:
        print("None")
    else:
        for row in missed:
            print(
                f"{row['side']:5} "
                f"{row['symbol']:20} "
                f"AI={row['score']:3} "
                f"RANK={row['rank']}"
            )

    print()
    print("===== FAILED =====")

    if not failed:
        print("None")
    else:
        for row in failed:
            print(
                row["symbol"],
                row["error"],
            )


if __name__ == "__main__":
    run_recall_test()
