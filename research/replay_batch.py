import json
import os

from replay.replay_config import (
    REPLAY_SYMBOLS,
    REPLAY_TIMEFRAME,
)

from research.research_runner import run_research

OUTPUT_FILE = "research/output/replay_batch.json"

os.makedirs("research/output", exist_ok=True)

results = []
skipped = []

print("=" * 70)
print("Replay Batch V3")
print("=" * 70)

for symbol in REPLAY_SYMBOLS:

    print(f"\nRunning {symbol}")

    try:

        result = run_research(
            symbols=[symbol],
            timeframe=REPLAY_TIMEFRAME,
            long_threshold=70,
            short_threshold=70,
            verbose=False,
        )

        result["symbol"] = symbol

        results.append(result)

        print(
            f"OK {symbol} "
            f"Signals={result['signals']} "
            f"Trades={result['trades']}"
        )

    except Exception as e:

        print(f"❌ Skip {symbol}: {e}")

        skipped.append({
            "symbol": symbol,
            "error": str(e)
        })

results = sorted(
    results,
    key=lambda x: (
        -x["trades"],
        -x["signals"]
    )
)

print()
print("=" * 70)
print("Replay Batch Summary")
print("=" * 70)

total_signal = 0
total_trade = 0

for r in results:

    total_signal += r["signals"]
    total_trade += r["trades"]

    print(
        f'{r["symbol"]:12}',
        f'S={r["signals"]:3}',
        f'T={r["trades"]:3}'
    )

print()
print("=" * 70)
print("TOTAL")
print("=" * 70)
print("Signals:", total_signal)
print("Trades :", total_trade)

print()
print("=" * 70)
print("SKIPPED")
print("=" * 70)

if skipped:
    for row in skipped:
        print(row["symbol"], row["error"])
else:
    print("None")

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        {
            "results": results,
            "skipped": skipped,
            "total": {
                "signals": total_signal,
                "trades": total_trade
            }
        },
        f,
        indent=4,
        ensure_ascii=False
    )

print()
print("Saved:")
print(OUTPUT_FILE)
