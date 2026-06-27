import csv
from datetime import datetime

START_TIME = "2026-06-26 17:45:00"
LOG_FILE = "trading_log_v2.csv"

def f(x):
    try:
        return float(x)
    except:
        return 0.0

closed = []

with open(LOG_FILE, newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for r in reader:
        t = r.get("time", "")
        reason = r.get("close_reason", "")
        if t >= START_TIME and ("TP3 已觸發" in reason or "止損已觸發" in reason):
            closed.append(r)

tp3 = [r for r in closed if "TP3 已觸發" in r.get("close_reason", "")]
sl = [r for r in closed if "止損已觸發" in r.get("close_reason", "")]

wins = [f(r.get("pnl", 0)) for r in closed if f(r.get("pnl", 0)) > 0]
losses = [f(r.get("pnl", 0)) for r in closed if f(r.get("pnl", 0)) < 0]

gross_profit = sum(wins)
gross_loss = sum(losses)
net_pnl = sum(f(r.get("pnl", 0)) for r in closed)
pf = gross_profit / abs(gross_loss) if gross_loss else 0
rate = len(tp3) / len(closed) * 100 if closed else 0

now = datetime.now()
start = datetime.strptime(START_TIME, "%Y-%m-%d %H:%M:%S")
hours = (now - start).total_seconds() / 3600

print("===== New Validation Statistics =====")
print(f"Start Time: {START_TIME}")
print(f"Runtime Hours: {hours:.2f}")
print(f"Valid Samples TP3/SL: {len(closed)}")
print(f"TP3: {len(tp3)}")
print(f"SL: {len(sl)}")
print(f"TP3 Rate: {rate:.2f}%")
print(f"Gross Profit: {gross_profit:.4f}")
print(f"Gross Loss: {gross_loss:.4f}")
print(f"Net PnL: {net_pnl:.4f}")
print(f"Profit Factor: {pf:.4f}")

print()
if hours >= 24:
    print("Time Target 24H: PASS")
else:
    print(f"Time Target 24H: Collecting, remaining {24-hours:.2f}h")

if len(closed) >= 30:
    print("Sample Target 30: PASS")
else:
    print(f"Sample Target 30: Collecting, remaining {30-len(closed)} samples")
