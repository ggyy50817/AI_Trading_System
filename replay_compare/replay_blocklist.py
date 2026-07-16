import csv

from replay_compare.config import START_TIME, LOG_FILE
from research.blocklist_engine import is_blocked


def f(x):
    try:
        return float(x)
    except:
        return 0.0


def load_blocklist_replay():

    original = 0
    blocked = 0
    kept = []

    with open(LOG_FILE, newline="", encoding="utf-8") as f:

        reader = csv.DictReader(f)

        for row in reader:

            if row["time"] < START_TIME:
                continue

            reason = row["close_reason"]

            if "TP3 已觸發" not in reason and \
               "止損已觸發" not in reason:
                continue

            original += 1

            if is_blocked(row["symbol"], row["side"]):
                blocked += 1
                continue

            kept.append(row)

    return original, blocked, kept


if __name__ == "__main__":

    original, blocked, kept = load_blocklist_replay()

    wins = [r for r in kept if f(r["pnl"]) > 0]
    losses = [r for r in kept if f(r["pnl"]) < 0]

    gp = sum(f(r["pnl"]) for r in wins)
    gl = abs(sum(f(r["pnl"]) for r in losses))
    pnl = gp - gl

    pf = gp / gl if gl else 0

    tp3 = len(wins)
    sl = len(losses)

    win_rate = tp3 / len(kept) * 100 if kept else 0

    print("=" * 70)
    print("Replay Blocklist")
    print("=" * 70)

    print(f"Original : {original}")
    print(f"Blocked  : {blocked}")
    print(f"Remain   : {len(kept)}")
    print()

    print(f"TP3      : {tp3}")
    print(f"SL       : {sl}")
    print(f"WinRate  : {win_rate:.2f}%")
    print(f"GrossProfit : {gp:.4f}")
    print(f"GrossLoss   : -{gl:.4f}")
    print(f"NetPnL      : {pnl:.4f}")
    print(f"PF          : {pf:.4f}")
