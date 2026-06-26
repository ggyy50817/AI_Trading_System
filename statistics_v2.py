import csv
from collections import defaultdict

START_TIME = "2026-06-23 03:29:00"
LOG_FILE = "trading_log_v2.csv"

def f(x):
    try:
        return float(x)
    except:
        return 0.0

def rate(a, b):
    return 0 if b == 0 else a / b * 100

def stat(title, rows):
    total = len(rows)
    wins = [r for r in rows if f(r["pnl"]) > 0]
    losses = [r for r in rows if f(r["pnl"]) < 0]
    gp = sum(f(r["pnl"]) for r in wins)
    gl = abs(sum(f(r["pnl"]) for r in losses))
    pnl = gp - gl
    pf = gp / gl if gl else 0

    print(f"\n===== {title} =====")
    print(f"Samples: {total}")
    print(f"Wins: {len(wins)}")
    print(f"Losses: {len(losses)}")
    print(f"Win Rate: {rate(len(wins), total):.2f}%")
    print(f"Gross Profit: {gp:.4f}")
    print(f"Gross Loss: -{gl:.4f}")
    print(f"Net PnL: {pnl:.4f}")
    print(f"Profit Factor: {pf:.4f}")

rows = []

with open(LOG_FILE, newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for r in reader:
        if r["time"] >= START_TIME:
            if "TP3 已觸發" in r["close_reason"] or "止損已觸發" in r["close_reason"]:
                rows.append(r)

print("===== Trading Statistics V2 =====")
print(f"Start Time: {START_TIME}")
print(f"Valid Samples: {len(rows)}")

stat("ALL", rows)
stat("LONG", [r for r in rows if r["side"] == "LONG"])
stat("SHORT", [r for r in rows if r["side"] == "SHORT"])

print("\n===== Symbol Deep Ranking =====")
by_symbol = defaultdict(list)

for r in rows:
    by_symbol[r["symbol"]].append(r)

ranking = []

for symbol, sample in by_symbol.items():
    wins = [r for r in sample if f(r["pnl"]) > 0]
    losses = [r for r in sample if f(r["pnl"]) < 0]
    gp = sum(f(r["pnl"]) for r in wins)
    gl = abs(sum(f(r["pnl"]) for r in losses))
    pnl = gp - gl
    pf = gp / gl if gl else 0
    ranking.append((pnl, symbol, len(sample), len(wins), len(losses), pf))

for pnl, symbol, total, wins, losses, pf in sorted(ranking, reverse=True):
    print(
        f"{symbol}: "
        f"Samples={total}, "
        f"Wins={wins}, "
        f"Losses={losses}, "
        f"WinRate={rate(wins,total):.2f}%, "
        f"PnL={pnl:.4f}, "
        f"PF={pf:.4f}"
    )

print("\n===== Worst LONG Symbols =====")
long_symbol = defaultdict(list)
for r in rows:
    if r["side"] == "LONG":
        long_symbol[r["symbol"]].append(r)

long_rank = []
for symbol, sample in long_symbol.items():
    pnl = sum(f(r["pnl"]) for r in sample)
    long_rank.append((pnl, symbol, len(sample)))

for pnl, symbol, total in sorted(long_rank):
    print(f"{symbol}: Samples={total}, PnL={pnl:.4f}")

print("\n===== Worst SHORT Symbols =====")
short_symbol = defaultdict(list)
for r in rows:
    if r["side"] == "SHORT":
        short_symbol[r["symbol"]].append(r)

short_rank = []
for symbol, sample in short_symbol.items():
    pnl = sum(f(r["pnl"]) for r in sample)
    short_rank.append((pnl, symbol, len(sample)))

for pnl, symbol, total in sorted(short_rank):
    print(f"{symbol}: Samples={total}, PnL={pnl:.4f}")

print("\n===== Daily Breakdown =====")
by_day = defaultdict(list)

for r in rows:
    by_day[r["time"][:10]].append(r)

for day in sorted(by_day):
    stat(day, by_day[day])
