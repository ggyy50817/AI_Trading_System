from collections import Counter

from penalty.penalty_engine import apply_penalty
from replay_compare.replay_original import load_original
from research.blocklist_engine import is_blocked

DEFAULT_THRESHOLD = 70


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def to_score(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def calculate_stats(rows):
    wins = [
        r for r in rows
        if to_float(r.get("pnl")) > 0
    ]

    losses = [
        r for r in rows
        if to_float(r.get("pnl")) < 0
    ]

    gross_profit = sum(
        to_float(r.get("pnl"))
        for r in wins
    )

    gross_loss = abs(
        sum(
            to_float(r.get("pnl"))
            for r in losses
        )
    )

    net_pnl = gross_profit - gross_loss

    profit_factor = (
        gross_profit / gross_loss
        if gross_loss else 0.0
    )

    win_rate = (
        len(wins) / len(rows) * 100
        if rows else 0.0
    )

    return {
        "samples": len(rows),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": win_rate,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "net_pnl": net_pnl,
        "profit_factor": profit_factor,
    }


def load_penalty_replay(
    threshold=DEFAULT_THRESHOLD
):
    original_rows = load_original()

    kept_rows = []
    blocked_rows = []
    penalty_filtered_rows = []
    penalty_filter_counter = Counter()

    for row in original_rows:
        symbol = row.get("symbol", "")
        side = row.get("side", "")

        if is_blocked(symbol, side):
            blocked_rows.append(row)
            continue

        score = to_score(
            row.get("ai_score")
        )

        penalty_result = apply_penalty(
            symbol=symbol,
            side=side,
            score=score,
        )

        if (
            penalty_result["penalty"] > 0
            and penalty_result["final_score"] < threshold
        ):
            penalty_filtered_rows.append(
                row
            )

            penalty_filter_counter[
                (side, symbol)
            ] += 1

            continue

        kept_rows.append(row)

    return {
        "original_rows": original_rows,
        "kept_rows": kept_rows,
        "blocked_rows": blocked_rows,
        "penalty_filtered_rows":
            penalty_filtered_rows,
        "penalty_filter_counter":
            penalty_filter_counter,
        "threshold": threshold,
    }


if __name__ == "__main__":
    result = load_penalty_replay()

    stats = calculate_stats(
        result["kept_rows"]
    )

    print("=" * 70)
    print("Replay Penalty V3")
    print("=" * 70)

    print(
        f"Threshold        : "
        f"{result['threshold']}"
    )

    print(
        f"Original         : "
        f"{len(result['original_rows'])}"
    )

    print(
        f"Blocklist Filter : "
        f"{len(result['blocked_rows'])}"
    )

    print(
        f"Penalty Filter   : "
        f"{len(result['penalty_filtered_rows'])}"
    )

    print(
        f"Remain           : "
        f"{stats['samples']}"
    )

    print()
    print(f"Wins         : {stats['wins']}")
    print(f"Losses       : {stats['losses']}")

    print(
        f"WinRate      : "
        f"{stats['win_rate']:.2f}%"
    )

    print(
        f"Gross Profit : "
        f"{stats['gross_profit']:.4f}"
    )

    print(
        f"Gross Loss   : "
        f"-{stats['gross_loss']:.4f}"
    )

    print(
        f"NetPnL       : "
        f"{stats['net_pnl']:.4f}"
    )

    print(
        f"PF           : "
        f"{stats['profit_factor']:.4f}"
    )

    print()
    print(
        "===== Penalty Filter Breakdown ====="
    )

    if not result["penalty_filter_counter"]:
        print("None")
    else:
        for (
            side,
            symbol
        ), count in sorted(
            result[
                "penalty_filter_counter"
            ].items(),
            key=lambda item: (
                -item[1],
                item[0][0],
                item[0][1],
            ),
        ):
            print(
                f"{side:5} "
                f"{symbol:12} "
                f"Filtered={count}"
            )

