"""
Shadow Statistics V1.1

Closed-sample statistics for Shadow Trading research.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


INPUT_PATH = Path("runtime/shadow/shadow_outcomes.jsonl")

CLOSED_RESULTS = {
    "STOP_LOSS",
    "TRAILING_STOP",
    "TP3",
}


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


def is_closed(row):
    return str(row.get("result")) in CLOSED_RESULTS


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
        wins = sum(
            1 for r in group
            if float(r.get("realized_pnl", 0) or 0) > 0
        )
        losses = sum(
            1 for r in group
            if float(r.get("realized_pnl", 0) or 0) < 0
        )
        pnl = sum(
            float(r.get("realized_pnl", 0) or 0)
            for r in group
        )

        win_rate = (
            wins / len(group) * 100
            if group else 0.0
        )

        print(
            f"{name}: "
            f"Closed={len(group)} "
            f"Wins={wins} "
            f"Losses={losses} "
            f"WinRate={win_rate:.2f}% "
            f"PnL={pnl:.4f} "
            f"PF={profit_factor(group):.4f}"
        )


def main():
    rows = load_outcomes()

    print("=" * 60)
    print("Shadow Statistics V1.1")
    print("=" * 60)

    if not rows:
        print("No shadow outcomes.")
        return

    closed_rows = [
        row for row in rows
        if is_closed(row)
    ]

    open_rows = [
        row for row in rows
        if str(row.get("status")) == "OPEN"
    ]

    no_future_rows = [
        row for row in rows
        if str(row.get("status")) == "NO_FUTURE_DATA"
    ]

    error_rows = [
        row for row in rows
        if str(row.get("status")) == "ERROR"
    ]

    wins = sum(
        1 for r in closed_rows
        if float(r.get("realized_pnl", 0) or 0) > 0
    )

    losses = sum(
        1 for r in closed_rows
        if float(r.get("realized_pnl", 0) or 0) < 0
    )

    pnl = sum(
        float(r.get("realized_pnl", 0) or 0)
        for r in closed_rows
    )

    win_rate = (
        wins / len(closed_rows) * 100
        if closed_rows else 0.0
    )

    print("Total Records:", len(rows))
    print("Closed Samples:", len(closed_rows))
    print("Open Samples:", len(open_rows))
    print("No Future Data:", len(no_future_rows))
    print("Errors:", len(error_rows))

    print()
    print("Closed Wins:", wins)
    print("Closed Losses:", losses)
    print(f"Closed Win Rate: {win_rate:.2f}%")
    print(f"Closed Net PnL: {pnl:.4f}")
    print(f"Closed Profit Factor: {profit_factor(closed_rows):.4f}")

    results = Counter(
        str(r.get("result", "UNKNOWN"))
        for r in closed_rows
    )

    print()
    print("===== Closed Results =====")

    for result, count in results.most_common():
        print(f"{result}: {count}")

    print_group(
        "LONG / SHORT - CLOSED ONLY",
        closed_rows,
        "side",
    )

    print_group(
        "Market Regime - CLOSED ONLY",
        closed_rows,
        "market_regime",
    )


if __name__ == "__main__":
    main()
