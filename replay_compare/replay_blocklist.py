from replay_compare.replay_original import load_original
from research.blocklist_engine import is_blocked


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def load_blocklist_replay():
    original_rows = load_original()

    blocked_rows = []
    kept_rows = []

    for row in original_rows:
        symbol = row.get("symbol", "")
        side = row.get("side", "")

        if is_blocked(symbol, side):
            blocked_rows.append(row)
            continue

        kept_rows.append(row)

    return {
        "original_rows": original_rows,
        "blocked_rows": blocked_rows,
        "kept_rows": kept_rows,
    }


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


if __name__ == "__main__":
    result = load_blocklist_replay()
    stats = calculate_stats(
        result["kept_rows"]
    )

    print("=" * 70)
    print("Replay Blocklist V3")
    print("=" * 70)

    print(
        f"Original : "
        f"{len(result['original_rows'])}"
    )

    print(
        f"Blocked  : "
        f"{len(result['blocked_rows'])}"
    )

    print(
        f"Remain   : "
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
