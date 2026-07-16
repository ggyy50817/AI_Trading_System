from collections import defaultdict

from validation_v2.log_loader import load_closed_trades


def f(x):
    try:
        return float(x)
    except:
        return 0.0


def calc(rows):
    total = len(rows)
    wins = [r for r in rows if f(r["pnl"]) > 0]
    losses = [r for r in rows if f(r["pnl"]) < 0]

    gp = sum(f(r["pnl"]) for r in wins)
    gl = abs(sum(f(r["pnl"]) for r in losses))
    pf = gp / gl if gl else 0
    pnl = gp - gl
    wr = len(wins) / total * 100 if total else 0

    return {
        "samples": total,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": wr,
        "gross_profit": gp,
        "gross_loss": gl,
        "net_pnl": pnl,
        "profit_factor": pf,
    }


rows = load_closed_trades()

by_side = defaultdict(list)
by_side_symbol = defaultdict(list)

for r in rows:
    side = r["side"]
    symbol = r["symbol"]

    by_side[side].append(r)
    by_side_symbol[(side, symbol)].append(r)

print("=" * 70)
print("LONG / SHORT Deep Analysis")
print("=" * 70)

for side in ["LONG", "SHORT"]:

    s = calc(by_side[side])

    print()
    print(f"===== {side} Overall =====")
    print(f"Samples : {s['samples']}")
    print(f"Wins    : {s['wins']}")
    print(f"Losses  : {s['losses']}")
    print(f"WinRate : {s['win_rate']:.2f}%")
    print(f"PF      : {s['profit_factor']:.4f}")
    print(f"NetPnL  : {s['net_pnl']:.4f}")

    print()
    print(f"===== Worst {side} Symbols =====")

    ranking = []

    for (side_key, symbol), sample in by_side_symbol.items():

        if side_key != side:
            continue

        stat = calc(sample)

        ranking.append((
            stat["profit_factor"],
            stat["net_pnl"],
            symbol,
            stat
        ))

    ranking.sort(key=lambda x: (x[0], x[1]))

    for pf, pnl, symbol, stat in ranking[:10]:

        print(
            f"{symbol:12} "
            f"Samples={stat['samples']:3} "
            f"WR={stat['win_rate']:.2f}% "
            f"PF={stat['profit_factor']:.4f} "
            f"PnL={stat['net_pnl']:.4f}"
        )

    print()
    print(f"===== Best {side} Symbols =====")

    ranking.sort(key=lambda x: (x[0], x[1]), reverse=True)

    for pf, pnl, symbol, stat in ranking[:10]:

        print(
            f"{symbol:12} "
            f"Samples={stat['samples']:3} "
            f"WR={stat['win_rate']:.2f}% "
            f"PF={stat['profit_factor']:.4f} "
            f"PnL={stat['net_pnl']:.4f}"
        )
