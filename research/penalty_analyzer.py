import csv
import json
import os
from collections import defaultdict

START_TIME = "2026-06-23 03:29:00"
LOG_FILE = "trading_log_v2.csv"
OUTPUT = "research/config/penalty.json"

stats = defaultdict(list)

with open(LOG_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:

        if row["time"] < START_TIME:
            continue

        reason = row["close_reason"]

        if "TP3 已觸發" not in reason and "止損已觸發" not in reason:
            continue

        stats[(row["side"], row["symbol"])].append(row)

result = {
    "LONG": {},
    "SHORT": {}
}

print("=" * 70)
print("Penalty Analyzer V2")
print("=" * 70)

for (side, symbol), rows in sorted(stats.items()):

    samples = len(rows)

    wins = [r for r in rows if float(r["pnl"]) > 0]
    losses = [r for r in rows if float(r["pnl"]) < 0]

    gp = sum(float(r["pnl"]) for r in wins)
    gl = abs(sum(float(r["pnl"]) for r in losses))

    pf = gp / gl if gl else 0
    wr = len(wins) / samples * 100

    penalty = 0

    if samples >= 15:

        if pf < 0.15:
            penalty = 20

        elif pf < 0.30:
            penalty = 15

        elif pf < 0.50:
            penalty = 10

        elif pf < 0.70:
            penalty = 5

    if penalty:

        result[side][symbol] = penalty

        print(
            f"{side:5} "
            f"{symbol:12} "
            f"S={samples:3} "
            f"PF={pf:.3f} "
            f"WR={wr:.2f}% "
            f"PENALTY={penalty}"
        )

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(
        result,
        f,
        indent=4,
        ensure_ascii=False
    )

print()
print("Saved:")
print(OUTPUT)
