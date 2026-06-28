import csv
from datetime import datetime
from collections import defaultdict

LOG_FILE = "trading_log_v2.csv"
START_TIME = datetime.strptime("2026-06-26 17:45:00", "%Y-%m-%d %H:%M:%S")
OUTPUT_FILE = "validation_report_v1.txt"

TP3_KEYWORD = "TP3 已觸發"
SL_KEYWORD = "止損已觸發"

def safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default

def parse_time(x):
    try:
        return datetime.strptime(x.strip(), "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

def is_valid_close(reason):
    return TP3_KEYWORD in reason or SL_KEYWORD in reason

def close_type(reason):
    if TP3_KEYWORD in reason:
        return "TP3"
    if SL_KEYWORD in reason:
        return "SL"
    return "OTHER"

def profit_factor(gross_profit, gross_loss):
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0
    return gross_profit / abs(gross_loss)

def pct(num, den):
    if den == 0:
        return 0
    return num / den * 100

rows = []

with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
    reader = csv.reader(f)
    for row in reader:
        if len(row) < 11:
            continue

        t = parse_time(row[0])
        if not t or t < START_TIME:
            continue

        symbol = row[1]
        side = row[2]
        pnl = safe_float(row[6])
        reason = row[10]

        if not is_valid_close(reason):
            continue

        result = close_type(reason)

        rows.append({
            "time": t,
            "date": t.strftime("%Y-%m-%d"),
            "symbol": symbol,
            "side": side,
            "pnl": pnl,
            "result": result,
            "reason": reason,
        })

total = len(rows)
tp3 = sum(1 for r in rows if r["result"] == "TP3")
sl = sum(1 for r in rows if r["result"] == "SL")

gross_profit = sum(r["pnl"] for r in rows if r["pnl"] > 0)
gross_loss = sum(r["pnl"] for r in rows if r["pnl"] < 0)
net_pnl = gross_profit + gross_loss
pf = profit_factor(gross_profit, gross_loss)

by_side = defaultdict(list)
by_symbol = defaultdict(list)
by_date = defaultdict(list)

for r in rows:
    by_side[r["side"]].append(r)
    by_symbol[r["symbol"]].append(r)
    by_date[r["date"]].append(r)

def summarize_group(group_rows):
    n = len(group_rows)
    win = sum(1 for r in group_rows if r["result"] == "TP3")
    loss = sum(1 for r in group_rows if r["result"] == "SL")
    gp = sum(r["pnl"] for r in group_rows if r["pnl"] > 0)
    gl = sum(r["pnl"] for r in group_rows if r["pnl"] < 0)
    np = gp + gl
    return {
        "samples": n,
        "tp3": win,
        "sl": loss,
        "tp3_rate": pct(win, n),
        "gross_profit": gp,
        "gross_loss": gl,
        "net_pnl": np,
        "pf": profit_factor(gp, gl),
    }

overall = summarize_group(rows)

lines = []
lines.append("=" * 70)
lines.append("BingX AI Trading System - Validation Report V1")
lines.append("=" * 70)
lines.append(f"Start Time: {START_TIME}")
lines.append(f"Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append("")
lines.append("===== 1. Overall Performance =====")
lines.append(f"Valid TP3/SL Samples: {overall['samples']}")
lines.append(f"TP3: {overall['tp3']}")
lines.append(f"SL: {overall['sl']}")
lines.append(f"TP3 Rate: {overall['tp3_rate']:.2f}%")
lines.append(f"Gross Profit: {overall['gross_profit']:.4f}")
lines.append(f"Gross Loss: {overall['gross_loss']:.4f}")
lines.append(f"Net PnL: {overall['net_pnl']:.4f}")
lines.append(f"Profit Factor: {overall['pf']:.4f}")
lines.append("")

lines.append("===== 2. LONG / SHORT Performance =====")
for side in ["LONG", "SHORT"]:
    s = summarize_group(by_side.get(side, []))
    lines.append(
        f"{side}: Samples={s['samples']}, TP3={s['tp3']}, SL={s['sl']}, "
        f"TP3Rate={s['tp3_rate']:.2f}%, NetPnL={s['net_pnl']:.4f}, PF={s['pf']:.4f}"
    )
lines.append("")

lines.append("===== 3. By Date =====")
for d in sorted(by_date.keys()):
    s = summarize_group(by_date[d])
    lines.append(
        f"{d}: Samples={s['samples']}, TP3={s['tp3']}, SL={s['sl']}, "
        f"TP3Rate={s['tp3_rate']:.2f}%, NetPnL={s['net_pnl']:.4f}, PF={s['pf']:.4f}"
    )
lines.append("")

lines.append("===== 4. Symbol Ranking =====")
symbol_stats = []
for sym, gr in by_symbol.items():
    s = summarize_group(gr)
    symbol_stats.append((sym, s))
symbol_stats.sort(key=lambda x: x[1]["net_pnl"], reverse=True)

for sym, s in symbol_stats:
    lines.append(
        f"{sym}: Samples={s['samples']}, TP3={s['tp3']}, SL={s['sl']}, "
        f"TP3Rate={s['tp3_rate']:.2f}%, NetPnL={s['net_pnl']:.4f}, PF={s['pf']:.4f}"
    )
lines.append("")

lines.append("===== 5. Critical Findings =====")

if overall["pf"] < 1:
    lines.append(f"- Overall PF={overall['pf']:.4f} < 1. Current strategy is negative expectancy in this validation window.")
else:
    lines.append(f"- Overall PF={overall['pf']:.4f} >= 1. Current validation window shows positive expectancy.")

long_s = summarize_group(by_side.get("LONG", []))
short_s = summarize_group(by_side.get("SHORT", []))

if long_s["samples"] > 0:
    lines.append(f"- LONG Engine: Samples={long_s['samples']}, TP3Rate={long_s['tp3_rate']:.2f}%, PF={long_s['pf']:.4f}, NetPnL={long_s['net_pnl']:.4f}.")
if short_s["samples"] > 0:
    lines.append(f"- SHORT Engine: Samples={short_s['samples']}, TP3Rate={short_s['tp3_rate']:.2f}%, PF={short_s['pf']:.4f}, NetPnL={short_s['net_pnl']:.4f}.")

worst = sorted(symbol_stats, key=lambda x: x[1]["net_pnl"])[:5]
best = sorted(symbol_stats, key=lambda x: x[1]["net_pnl"], reverse=True)[:5]

lines.append("- Worst 5 symbols by Net PnL:")
for sym, s in worst:
    lines.append(f"  - {sym}: NetPnL={s['net_pnl']:.4f}, Samples={s['samples']}, PF={s['pf']:.4f}")

lines.append("- Best 5 symbols by Net PnL:")
for sym, s in best:
    lines.append(f"  - {sym}: NetPnL={s['net_pnl']:.4f}, Samples={s['samples']}, PF={s['pf']:.4f}")

lines.append("")
lines.append("===== 6. Strategy Decisions Suggested =====")
lines.append("1. Do NOT move to LIVE trading yet.")
lines.append("2. Prioritize filtering bad trades before adding new indicators.")
lines.append("3. Build Blocklist / Penalty research from worst symbols and losing clusters.")
lines.append("4. Validate Reverse Engine only with historical data first; do not directly flip live trades.")
lines.append("5. Keep risk controls unchanged: no higher leverage, no lower thresholds, no larger single/total risk.")
lines.append("")

lines.append("===== 7. Next Development Order =====")
lines.append("P0: Review this Validation Report V1.")
lines.append("P1: Add Validation Statistics V2 for AI Score / Funding / OI / ATR / Volume / MA20 / Market Regime clusters.")
lines.append("P2: Build Blocklist Engine.")
lines.append("P3: Build Penalty Engine.")
lines.append("P4: Research Reverse Engine / Anti-AI Strategy in VST only.")
lines.append("P5: Revisit Market Regime V2.")
lines.append("P6: Position Size Engine after strategy filtering improves.")
lines.append("")

report = "\n".join(lines)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(report)

print(report)
print("")
print(f"Saved report to: {OUTPUT_FILE}")
