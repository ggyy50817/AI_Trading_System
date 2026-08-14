"""
Shadow Statistics V1
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


INPUT_PATH = Path("runtime/shadow/shadow_outcomes.jsonl")


def load_outcomes():
    rows = []

    if not INPUT_PATH.exists():
        return rows

    with INPUT_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    return rows


def profit_factor(rows):
    gross_profit = sum(
        float(r.get("realized_pnl", 0) or 0)
        for r in rows
        if float(r.get("realized_pnl", 0) or 0) > 0
    )

    gross_loss = abs(
        sum(
            float(r.get("realized_pnl", 0) or 0)
            for r in rows
            if float(r.get("realized_pnl", 0) or 0) < 0
        )
    )

    return gross_profit / gross_loss if gross_loss else 0.0


def print_group(title, rows, key):
    groups = defaultdict(list)

    for row in rows:
        groups[str(row.get(key, "UNKNOWN"))].append(row)

    print()
    print(f"===== {title} =====")

    for name, group in sorted(groups.items()):
        pnl = sum(float(r.get("realized_pnl", 0) or 0) for r in group)
        wins = sum(
            1 for r in group
            if float(r.get("realized_pnl", 0) or 0) > 0
        )

        print(
            f"{name}: "
            f"Samples={len(group)} "
            f"WinRate={wins / len(group) * 100:.2f}% "
            f"PnL={pnl:.4f} "
            f"PF={profit_factor(group):.4f}"
        )


def main():
    rows = load_outcomes()

    print("=" * 60)
    print("Shadow Statistics V1")
    print("=" * 60)

    if not rows:
        print("No shadow outcomes.")
        return

    pnl = sum(float(r.get("realized_pnl", 0) or 0) for r in rows)
    wins = sum(
        1 for r in rows
        if float(r.get("realized_pnl", 0) or 0) > 0
    )
    losses = sum(
        1 for r in rows
        if float(r.get("realized_pnl", 0) or 0) < 0
    )

    results = Counter(
        str(r.get("result", "UNKNOWN"))
        for r in rows
    )

    print("Samples:", len(rows))
    print("Wins:", wins)
    print("Losses:", losses)
    print(f"Win Rate: {wins / len(rows) * 100:.2f}%")
    print(f"Net PnL: {pnl:.4f}")
    print(f"Profit Factor: {profit_factor(rows):.4f}")

    print()
    print("===== Results =====")

    for result, count in results.most_common():
        print(f"{result}: {count}")

    print_group("LONG / SHORT", rows, "side")
    print_group("Market Regime", rows, "market_regime")


if __name__ == "__main__":
    main()
