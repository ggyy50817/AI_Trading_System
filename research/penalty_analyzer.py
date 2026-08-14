import csv
import json
import os
from collections import defaultdict

START_TIME = "2026-06-23 03:29:00"
LOG_FILE = "trading_log_v3.csv"
OUTPUT = "research/config/penalty.json"

stats = defaultdict(list)

with open(LOG_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        if row.get("time", "") < START_TIME:
            continue

        if row.get("action") != "FULL_CLOSE":
            continue

        reason = row.get("close_reason", "")

        if (
            "TP3 已觸發" not in reason
            and "止損已觸發" not in reason
        ):
            continue

        market = str(
            row.get("market_regime", "UNKNOWN")
        )

        try:
            score = int(
                float(row.get("ai_score", 0))
            )
        except (TypeError, ValueError):
            continue

        # Exclude legacy rows without valid AI Context.
        if score == 0 and market == "UNKNOWN":
            continue

        side = row.get("side", "UNKNOWN")
        symbol = row.get("symbol", "UNKNOWN")

        stats[(side, symbol)].append(row)

result = {
    "LONG": {},
    "SHORT": {}
}

print("=" * 70)
print("Penalty Analyzer V3")
print("=" * 70)

total_valid = sum(
    len(rows)
    for rows in stats.values()
)

print("Valid Context Samples:", total_valid)
print()

for (side, symbol), rows in sorted(stats.items()):
    samples = len(rows)

    wins = [
        r for r in rows
        if float(r.get("pnl", 0)) > 0
    ]

    losses = [
        r for r in rows
        if float(r.get("pnl", 0)) < 0
    ]

    gp = sum(
        float(r.get("pnl", 0))
        for r in wins
    )

    gl = abs(
        sum(
            float(r.get("pnl", 0))
            for r in losses
        )
    )

    pf = gp / gl if gl else 0
    wr = (
        len(wins) / samples * 100
        if samples else 0
    )

    penalty = 0

    # Existing Penalty V2 rules preserved.
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
        result.setdefault(side, {})
        result[side][symbol] = penalty

        print(
            f"{side:5} "
            f"{symbol:12} "
            f"S={samples:3} "
            f"PF={pf:.3f} "
            f"WR={wr:.2f}% "
            f"PENALTY={penalty}"
        )

os.makedirs(
    os.path.dirname(OUTPUT),
    exist_ok=True
)

with open(
    OUTPUT,
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
print(OUTPUT)
