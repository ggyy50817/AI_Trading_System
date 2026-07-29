"""AI Score Debug — scan WATCHLIST and print score breakdowns to console.

Uses existing ``scanner.ai_score.calculate_ai_context`` only.
Does not modify trading logic or write any files.
"""

from __future__ import annotations

from collections import Counter

from scanner.ai_score import calculate_ai_context
from scanner.scanner import WATCHLIST


def run_ai_score_debug() -> None:
    results: list[dict] = []

    print("=" * 60)
    print("AI Score Debug")
    print("=" * 60)

    for symbol in WATCHLIST:
        try:
            ctx = calculate_ai_context(symbol)
        except Exception as e:
            print(f"\n[{symbol}] ERROR: {e}")
            continue

        results.append(ctx)

        print()
        print(f"Symbol          : {ctx.get('symbol', symbol)}")
        print(f"Market Regime   : {ctx.get('market_regime')}")
        print(f"MA20 Position   : {ctx.get('ma20_position')}")
        print(f"Volume Spike    : {ctx.get('volume_spike')}")
        print(f"Funding Status  : {ctx.get('funding_status')}")
        print(f"OI Status       : {ctx.get('oi_status')}")
        print(f"ATR Status      : {ctx.get('atr_status')}")
        print(f"Final AI Score  : {ctx.get('score')}")
        print("-" * 40)

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    if not results:
        print("No results.")
        return

    score_dist = Counter(r.get("score") for r in results)
    print("Score Distribution:")
    for score, count in sorted(score_dist.items(), key=lambda x: (x[0] is None, x[0])):
        print(f"  {score}: {count}")

    ma20_true = sum(1 for r in results if r.get("ma20_position") == "ABOVE")
    volume_spike_count = sum(1 for r in results if r.get("volume_spike") is True)
    funding_counts = Counter(r.get("funding_status") for r in results)
    oi_normal = sum(1 for r in results if r.get("oi_status") == "資料正常")
    atr_normal = sum(1 for r in results if r.get("atr_status") == "波動正常")

    print(f"MA20 True Count      : {ma20_true}")
    print(f"Volume Spike Count   : {volume_spike_count}")
    print("Funding Status Count :")
    for status, count in sorted(funding_counts.items(), key=lambda x: str(x[0])):
        print(f"  {status}: {count}")
    print(f"OI Normal Count      : {oi_normal}")
    print(f"ATR Normal Count     : {atr_normal}")
    print(f"Total Symbols        : {len(results)}")


if __name__ == "__main__":
    run_ai_score_debug()
