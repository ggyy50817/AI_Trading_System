import csv
import subprocess
from collections import defaultdict

START_TIME = "2026-06-23 03:29:00"
LOG_FILE = "trading_log_v2.csv"

def f(x):
    try:
        return float(x)
    except:
        return 0.0

rows = []
with open(LOG_FILE, newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for r in reader:
        if r["time"] >= START_TIME:
            rows.append(r)

closed = [
    r for r in rows
    if "TP3 已觸發" in r["close_reason"] or "止損已觸發" in r["close_reason"]
]

tp3 = [r for r in closed if "TP3 已觸發" in r["close_reason"]]
sl = [r for r in closed if "止損已觸發" in r["close_reason"]]

wins = [f(r["pnl"]) for r in closed if f(r["pnl"]) > 0]
losses = [f(r["pnl"]) for r in closed if f(r["pnl"]) < 0]

gross_profit = sum(wins)
gross_loss = abs(sum(losses))
net_pnl = sum(f(r["pnl"]) for r in closed)
pf = gross_profit / gross_loss if gross_loss else 0

def rate(a, b):
    return 0 if b == 0 else a / b * 100

def group_stats(name, sample):
    t = len(sample)
    w = [r for r in sample if f(r["pnl"]) > 0]
    l = [r for r in sample if f(r["pnl"]) < 0]
    pnl = sum(f(r["pnl"]) for r in sample)
    gp = sum(f(r["pnl"]) for r in w)
    gl = abs(sum(f(r["pnl"]) for r in l))
    pf = gp / gl if gl else 0
    print(f"{name}: Samples={t}, Win={len(w)}, Loss={len(l)}, WinRate={rate(len(w),t):.2f}%, PnL={pnl:.4f}, PF={pf:.4f}")

print("===== B Group Milestone Report =====")
print(f"Start Time: {START_TIME}")
print(f"Total Rows: {len(rows)}")
print(f"Valid Samples TP3/SL: {len(closed)}")
print(f"TP3: {len(tp3)}")
print(f"SL: {len(sl)}")
print(f"TP3 Rate: {rate(len(tp3), len(closed)):.2f}%")
print(f"Gross Profit: {gross_profit:.4f}")
print(f"Gross Loss: -{gross_loss:.4f}")
print(f"Net PnL: {net_pnl:.4f}")
print(f"Profit Factor: {pf:.4f}")

print("\n===== LONG / SHORT =====")
group_stats("LONG", [r for r in closed if r["side"] == "LONG"])
group_stats("SHORT", [r for r in closed if r["side"] == "SHORT"])

print("\n===== By Date =====")
by_date = defaultdict(list)
for r in closed:
    by_date[r["time"][:10]].append(r)
for d in sorted(by_date):
    group_stats(d, by_date[d])

print("\n===== Symbol Ranking =====")
by_symbol = defaultdict(list)
for r in closed:
    by_symbol[r["symbol"]].append(r)

symbol_rows = []
for s, sample in by_symbol.items():
    pnl = sum(f(r["pnl"]) for r in sample)
    wins = sum(1 for r in sample if f(r["pnl"]) > 0)
    total = len(sample)
    symbol_rows.append((pnl, s, total, wins))

for pnl, s, total, wins in sorted(symbol_rows, reverse=True):
    print(f"{s}: PnL={pnl:.4f}, Samples={total}, WinRate={rate(wins,total):.2f}%")

print("\n===== Current Positions =====")
try:
    from scanner.bingx_vst_api import get_vst_positions
    data = get_vst_positions()
    positions = data.get("data", [])
    print(f"Open Positions: {len(positions)}")
    total_value = 0
    total_unrealized = 0
    for p in positions:
        value = f(p.get("positionValue", 0))
        pnl = f(p.get("unrealizedProfit", 0))
        total_value += value
        total_unrealized += pnl
        print(p.get("symbol"), p.get("positionSide"), "PnL=", p.get("unrealizedProfit"), "Value=", p.get("positionValue"))
    print(f"Total Position Value: {total_value:.4f}")
    print(f"Total Unrealized PnL: {total_unrealized:.4f}")
except Exception as e:
    print("Position check failed:", e)

print("\n===== Bot Status =====")
try:
    print(subprocess.getoutput("ps -ef | grep main.py | grep -v grep"))
    print(subprocess.getoutput("tmux ls"))
except Exception as e:
    print("Bot status check failed:", e)
