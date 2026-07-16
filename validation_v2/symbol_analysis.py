import json
import os
from collections import defaultdict

from validation_v2.log_loader import load_closed_trades


def f(x):
    try:
        return float(x)
    except:
        return 0.0


rows = load_closed_trades()

symbols = defaultdict(list)

for r in rows:
    symbols[r["symbol"]].append(r)

result = {}

print("=" * 70)
print("Symbol Analysis V2")
print("=" * 70)

for symbol, sample in sorted(symbols.items()):

    wins = [r for r in sample if f(r["pnl"]) > 0]
    losses = [r for r in sample if f(r["pnl"]) < 0]

    gp = sum(f(r["pnl"]) for r in wins)
    gl = abs(sum(f(r["pnl"]) for r in losses))
    pnl = gp - gl
    pf = gp / gl if gl else 0
    wr = len(wins) / len(sample) * 100 if sample else 0

    result[symbol] = {
        "samples": len(sample),
        "wins": len(wins),
        "losses": len(losses),
        "tp3": len(wins),
        "sl": len(losses),
        "win_rate": round(wr, 2),
        "gross_profit": round(gp, 4),
        "gross_loss": round(-gl, 4),
        "net_pnl": round(pnl, 4),
        "profit_factor": round(pf, 4),
    }

ranking = sorted(
    result.items(),
    key=lambda x: x[1]["profit_factor"],
    reverse=True
)

print()
print("===== Ranking by Profit Factor =====")

for symbol, s in ranking:

    print(
        f"{symbol:12} "
        f"S={s['samples']:3} "
        f"WR={s['win_rate']:6.2f}% "
        f"PF={s['profit_factor']:.4f} "
        f"PnL={s['net_pnl']:.4f}"
    )

os.makedirs("validation_v2/output", exist_ok=True)

with open(
    "validation_v2/output/symbol_analysis.json",
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
print("validation_v2/output/symbol_analysis.json")
