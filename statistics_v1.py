import csv
from collections import defaultdict

START_DATE = "2026-06-19"

rows = []

with open("trading_log_v2.csv", newline='', encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        if r["time"] >= START_DATE:
            rows.append(r)

closed = [
    r for r in rows
    if "TP3 已觸發" in r["close_reason"] or "止損已觸發" in r["close_reason"]
]

tp3 = [r for r in closed if "TP3 已觸發" in r["close_reason"]]
sl = [r for r in closed if "止損已觸發" in r["close_reason"]]

longs = [r for r in closed if r["side"] == "LONG"]
shorts = [r for r in closed if r["side"] == "SHORT"]

wins = [float(r["pnl"]) for r in closed if float(r["pnl"]) > 0]
losses = [float(r["pnl"]) for r in closed if float(r["pnl"]) < 0]

gross_profit = sum(wins)
gross_loss = abs(sum(losses))
profit_factor = 0 if gross_loss == 0 else gross_profit / gross_loss

def rate(a, b):
    return 0 if b == 0 else a / b * 100

def win_rate(sample):
    if len(sample) == 0:
        return 0
    wins_count = sum(1 for r in sample if float(r["pnl"]) > 0)
    return wins_count / len(sample) * 100

by_symbol = defaultdict(float)
for r in closed:
    by_symbol[r["symbol"]] += float(r["pnl"])

best_symbol = max(by_symbol.items(), key=lambda x: x[1]) if by_symbol else ("N/A", 0)
worst_symbol = min(by_symbol.items(), key=lambda x: x[1]) if by_symbol else ("N/A", 0)

print("===== Trading Statistics V1.1 =====")
print(f"Start Date: {START_DATE}")
print(f"Total Rows All Actions: {len(rows)}")
print(f"Valid Closed Samples TP3/SL: {len(closed)}")
print(f"TP3 Count: {len(tp3)}")
print(f"SL Count: {len(sl)}")
print(f"TP3 Rate: {rate(len(tp3), len(closed)):.2f}%")

print("\n===== PnL =====")
print(f"Closed PnL TP3/SL: {sum(float(r['pnl']) for r in closed):.4f}")
print(f"Gross Profit: {gross_profit:.4f}")
print(f"Gross Loss: -{gross_loss:.4f}")
print(f"Profit Factor: {profit_factor:.4f}")

print("\n===== LONG / SHORT =====")
print(f"LONG Samples: {len(longs)}")
print(f"SHORT Samples: {len(shorts)}")
print(f"LONG Win Rate: {win_rate(longs):.2f}%")
print(f"SHORT Win Rate: {win_rate(shorts):.2f}%")
print(f"LONG PnL: {sum(float(r['pnl']) for r in longs):.4f}")
print(f"SHORT PnL: {sum(float(r['pnl']) for r in shorts):.4f}")

print("\n===== Average =====")
print(f"Average Win: {(gross_profit / len(wins)) if wins else 0:.4f}")
print(f"Average Loss: {(sum(losses) / len(losses)) if losses else 0:.4f}")

print("\n===== Best / Worst Symbol =====")
print(f"Best Symbol: {best_symbol[0]} {best_symbol[1]:.4f}")
print(f"Worst Symbol: {worst_symbol[0]} {worst_symbol[1]:.4f}")

print("\n===== Symbol Ranking =====")
for symbol, pnl in sorted(by_symbol.items(), key=lambda x: x[1], reverse=True):
    print(f"{symbol}: {pnl:.4f}")
