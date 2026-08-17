"""
Shadow Context Statistics V1

Analyze CLOSED Shadow Context outcomes.

Research only:
- No live trading
- No strategy modification
- No automatic parameter changes
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path(
    "runtime/shadow/shadow_context_outcomes.jsonl"
)


def load_closed_context_rows(
    path: Path = DEFAULT_INPUT,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    if not path.exists():
        return rows

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue

            if row.get("status") != "CLOSED":
                continue

            if not isinstance(row.get("context"), dict):
                continue

            rows.append(row)

    return rows


def pnl(row: dict[str, Any]) -> float:
    return float(row.get("realized_pnl") or 0.0)


def profit_factor(rows: list[dict[str, Any]]) -> float | None:
    gross_profit = sum(
        pnl(row)
        for row in rows
        if pnl(row) > 0
    )

    gross_loss = abs(
        sum(
            pnl(row)
            for row in rows
            if pnl(row) < 0
        )
    )

    if gross_loss == 0:
        return None

    return gross_profit / gross_loss


def summarize(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    samples = len(rows)

    wins = sum(
        1 for row in rows
        if pnl(row) > 0
    )

    losses = sum(
        1 for row in rows
        if pnl(row) < 0
    )

    breakeven = samples - wins - losses

    net_pnl = sum(
        pnl(row)
        for row in rows
    )

    return {
        "samples": samples,
        "wins": wins,
        "losses": losses,
        "breakeven": breakeven,
        "win_rate": (
            wins / samples * 100
            if samples else 0.0
        ),
        "net_pnl": net_pnl,
        "expectancy": (
            net_pnl / samples
            if samples else 0.0
        ),
        "profit_factor": profit_factor(rows),
    }


def group_by(
    rows: list[dict[str, Any]],
    key_func,
) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        key = str(key_func(row))
        groups[key].append(row)

    return dict(groups)


def print_summary(
    title: str,
    rows: list[dict[str, Any]],
) -> None:
    stats = summarize(rows)

    pf = stats["profit_factor"]
    pf_text = (
        "INF"
        if pf is None
        else f"{pf:.3f}"
    )

    print(
        f"{title:<25} "
        f"N={stats['samples']:<4} "
        f"W={stats['wins']:<4} "
        f"L={stats['losses']:<4} "
        f"WR={stats['win_rate']:.2f}% "
        f"PnL={stats['net_pnl']:.4f} "
        f"EXP={stats['expectancy']:.4f} "
        f"PF={pf_text}"
    )


def print_group(
    title: str,
    groups: dict[str, list[dict[str, Any]]],
) -> None:
    print()
    print("=" * 90)
    print(title)
    print("=" * 90)

    for key in sorted(groups):
        print_summary(
            key,
            groups[key],
        )


def main() -> None:
    rows = load_closed_context_rows()

    print("=" * 90)
    print("Shadow Context Statistics V1")
    print("=" * 90)

    if not rows:
        print("No CLOSED context outcomes found.")
        return

    print_summary("ALL", rows)

    print_group(
        "SIDE",
        group_by(
            rows,
            lambda r: r.get("side", "UNKNOWN"),
        ),
    )

    print_group(
        "AI SCORE",
        group_by(
            rows,
            lambda r: r.get("ai_score", "UNKNOWN"),
        ),
    )

    print_group(
        "MA20 POSITION",
        group_by(
            rows,
            lambda r: r["context"].get(
                "ma20_position",
                "UNKNOWN",
            ),
        ),
    )

    print_group(
        "VOLUME SPIKE",
        group_by(
            rows,
            lambda r: r["context"].get(
                "volume_spike",
                "UNKNOWN",
            ),
        ),
    )

    print_group(
        "FUNDING STATUS",
        group_by(
            rows,
            lambda r: r["context"].get(
                "funding_status",
                "UNKNOWN",
            ),
        ),
    )

    print_group(
        "OI STATUS",
        group_by(
            rows,
            lambda r: r["context"].get(
                "oi_status",
                "UNKNOWN",
            ),
        ),
    )

    print_group(
        "ATR STATUS",
        group_by(
            rows,
            lambda r: r["context"].get(
                "atr_status",
                "UNKNOWN",
            ),
        ),
    )


if __name__ == "__main__":
    main()