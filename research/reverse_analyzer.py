import json

from statistics.engine import build_statistics

print("=" * 70)
print("Reverse Analyzer V1")
print("=" * 70)

stats = build_statistics()

symbols = stats["by_symbol"]

ranking = []

for symbol, s in symbols.items():

    ranking.append(
        (
            s["profit_factor"],
            s["win_rate"],
            s["net_pnl"],
            symbol,
            s
        )
    )

ranking.sort()

print()
print("===== Worst Symbols =====")
print()

for pf, wr, pnl, symbol, s in ranking[:10]:

    print(
        f"{symbol:12} "
        f"PF={pf:.3f} "
        f"WR={wr:.2f}% "
        f"PnL={pnl:.4f}"
    )

print()
print("=" * 70)
print("Suggestions")
print("=" * 70)

blocklist = []
penalty = []
reverse = []

for pf, wr, pnl, symbol, s in ranking:

    if s["samples"] < 5:
        continue

    if pf < 0.20:

        blocklist.append(symbol)

    elif pf < 0.40:

        penalty.append(symbol)

    elif wr < 25:

        reverse.append(symbol)

result = {
    "blocklist": blocklist,
    "penalty": penalty,
    "reverse_research": reverse
}

print(json.dumps(
    result,
    indent=4,
    ensure_ascii=False
))

with open(
    "research/output/reverse_analysis.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        result,
        f,
        indent=4,
        ensure_ascii=False
    )

print()
print("Saved:")
print("research/output/reverse_analysis.json")
