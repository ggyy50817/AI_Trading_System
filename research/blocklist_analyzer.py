import csv
import json
from collections import defaultdict

from research.blocklist_engine import save_blocklist

LOG_FILE = "trading_log_v3.csv"
START_TIME = "2026-06-23 03:29:00"
RULE_FILE = "research/config/blocklist_rules.json"

with open(RULE_FILE, "r", encoding="utf-8") as f:
    rules = json.load(f)

MIN_SAMPLE = rules["min_samples"]
PF_LIMIT = rules["pf_limit"]
WIN_RATE_LIMIT = rules["win_rate_limit"]


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


rows = []
invalid_context = 0

with open(LOG_FILE, newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)

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

        market = str(row.get("market_regime", "UNKNOWN"))

        try:
            score = int(float(row.get("ai_score", 0)))
        except (TypeError, ValueError):
            invalid_context += 1
            continue

        # Exclude legacy samples without complete AI Context.
        if score == 0 and market == "UNKNOWN":
            invalid_context += 1
            continue

        rows.append(row)


groups = defaultdict(list)

for row in rows:
    groups[
        (
            row.get("side", "UNKNOWN"),
            row.get("symbol", "UNKNOWN"),
        )
    ].append(row)


result = {
    "LONG": {},
    "SHORT": {},
}


print("=" * 70)
print("Blocklist Analyzer V3")
print("=" * 70)
print(f"Valid Context Samples: {len(rows)}")
print(f"Invalid Context: {invalid_context}")
print(f"Min Samples: {MIN_SAMPLE}")
print(f"PF Limit: {PF_LIMIT}")
print(f"Win Rate Limit: {WIN_RATE_LIMIT}%")
print()


for (side, symbol), sample in sorted(groups.items()):
    total = len(sample)

    wins = [
        row
        for row in sample
        if to_float(row.get("pnl")) > 0
    ]

    losses = [
        row
        for row in sample
        if to_float(row.get("pnl")) < 0
    ]

    gross_profit = sum(
        to_float(row.get("pnl"))
        for row in wins
    )

    gross_loss = abs(
        sum(
            to_float(row.get("pnl"))
            for row in losses
        )
    )

    pf = (
        gross_profit / gross_loss
        if gross_loss > 0
        else 0.0
    )

    win_rate = (
        len(wins) / total * 100
        if total else 0.0
    )

    if (
        total >= MIN_SAMPLE
        and pf < PF_LIMIT
        and win_rate < WIN_RATE_LIMIT
    ):
        result.setdefault(side, {})

        result[side][symbol] = {
            "samples": total,
            "pf": round(pf, 4),
            "win_rate": round(win_rate, 2),
        }

        print(
            f"{side:5} "
            f"{symbol:12} "
            f"S={total:3} "
            f"PF={pf:.4f} "
            f"WR={win_rate:.2f}%"
        )


save_blocklist(result)

print()
print("Blocked LONG:", len(result["LONG"]))
print("Blocked SHORT:", len(result["SHORT"]))
print()
print("Saved:")
print("research/config/blocklist.json")
