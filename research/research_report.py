import json
import os

from statistics.engine import build_statistics

OUTPUT = "research/output/research_report_v2.md"

stats = build_statistics()

all_stat = stats["all"]
side = stats["by_side"]
symbol = stats["by_symbol"]

os.makedirs("research/output", exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as f:

    f.write("# Research Report V2\n\n")

    f.write("## Overall\n\n")

    f.write(f"- Samples: {all_stat['samples']}\n")
    f.write(f"- TP3: {all_stat['tp3']}\n")
    f.write(f"- SL: {all_stat['sl']}\n")
    f.write(f"- WinRate: {all_stat['win_rate']}%\n")
    f.write(f"- ProfitFactor: {all_stat['profit_factor']}\n")
    f.write(f"- NetPnL: {all_stat['net_pnl']}\n\n")

    f.write("## LONG\n\n")

    if "LONG" in side:
        for k, v in side["LONG"].items():
            f.write(f"- {k}: {v}\n")

    f.write("\n")

    f.write("## SHORT\n\n")

    if "SHORT" in side:
        for k, v in side["SHORT"].items():
            f.write(f"- {k}: {v}\n")

    f.write("\n")

    ranking = sorted(
        symbol.items(),
        key=lambda x: x[1]["profit_factor"]
    )

    f.write("## Worst Symbols\n\n")

    for name, s in ranking[:10]:

        f.write(
            f"- {name} "
            f"(PF={s['profit_factor']}, "
            f"WR={s['win_rate']}%, "
            f"PnL={s['net_pnl']})\n"
        )

    f.write("\n")

    f.write("## Best Symbols\n\n")

    for name, s in ranking[::-1][:10]:

        f.write(
            f"- {name} "
            f"(PF={s['profit_factor']}, "
            f"WR={s['win_rate']}%, "
            f"PnL={s['net_pnl']})\n"
        )

print("=" * 60)
print("Research Report V2")
print("=" * 60)
print("Saved:")
print(OUTPUT)
