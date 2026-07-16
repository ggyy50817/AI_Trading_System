import json
import os

from validation_v2.log_loader import load_closed_trades
from validation_v2.side_analysis import calc

rows = load_closed_trades()

overall = calc(rows)
long_stat = calc([r for r in rows if r["side"] == "LONG"])
short_stat = calc([r for r in rows if r["side"] == "SHORT"])

with open(
    "validation_v2/output/symbol_analysis.json",
    encoding="utf-8"
) as f:
    symbols = json.load(f)

ranking = sorted(
    symbols.items(),
    key=lambda x: x[1]["profit_factor"],
    reverse=True
)

best = ranking[:5]
worst = ranking[-5:]

report = []

report.append("# Validation Report V2")
report.append("")
report.append("## Overall")
report.append(f"- Samples: {overall['samples']}")
report.append(f"- WinRate: {overall['win_rate']:.2f}%")
report.append(f"- ProfitFactor: {overall['profit_factor']:.4f}")
report.append(f"- NetPnL: {overall['net_pnl']:.4f}")
report.append("")

report.append("## LONG")
for k, v in long_stat.items():
    report.append(f"- {k}: {v}")

report.append("")
report.append("## SHORT")
for k, v in short_stat.items():
    report.append(f"- {k}: {v}")

report.append("")
report.append("## Best Symbols")
for s, stat in best:
    report.append(
        f"- {s} | PF={stat['profit_factor']} | WR={stat['win_rate']}% | PnL={stat['net_pnl']}"
    )

report.append("")
report.append("## Worst Symbols")
for s, stat in worst:
    report.append(
        f"- {s} | PF={stat['profit_factor']} | WR={stat['win_rate']}% | PnL={stat['net_pnl']}"
    )

report.append("")
report.append("## Suggestions")

if long_stat["profit_factor"] < 0.3:
    report.append("- LONG Strategy needs major improvement.")

if short_stat["profit_factor"] < 1:
    report.append("- SHORT Strategy should be optimized further.")

if worst:
    report.append(
        "- Blocklist candidates: "
        + ", ".join([s for s, _ in worst])
    )

if best:
    report.append(
        "- Keep observing: "
        + ", ".join([s for s, _ in best])
    )

os.makedirs("validation_v2/output", exist_ok=True)

path = "validation_v2/output/Validation_Report_V2.md"

with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(report))

print("=" * 60)
print("Validation Report V2")
print("=" * 60)
print(f"Saved: {path}")
print()
print("================ Preview ================")
print()

for line in report[:40]:
    print(line)
