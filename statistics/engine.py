import csv
import json
import os
from collections import defaultdict

DEFAULT_LOG_FILE = "trading_log_v2.csv"
DEFAULT_START_TIME = "2026-06-23 03:29:00"

def f(x):
    try:
        return float(x)
    except:
        return 0.0

def rate(a, b):
    return 0 if b == 0 else a / b * 100

def load_closed_samples(
    log_file=DEFAULT_LOG_FILE,
    start_time=DEFAULT_START_TIME,
):
    rows = []

    if not os.path.exists(log_file):
        return rows

    with open(log_file, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for r in reader:
            if r.get("time", "") >= start_time:
                reason = r.get("close_reason", "")
                if "TP3 已觸發" in reason or "止損已觸發" in reason:
                    rows.append(r)

    return rows

def calc_stats(rows):
    total = len(rows)
    wins = [r for r in rows if f(r.get("pnl", 0)) > 0]
    losses = [r for r in rows if f(r.get("pnl", 0)) < 0]

    gp = sum(f(r.get("pnl", 0)) for r in wins)
    gl = abs(sum(f(r.get("pnl", 0)) for r in losses))
    net = gp - gl
    pf = gp / gl if gl else 0

    tp3 = [r for r in rows if "TP3 已觸發" in r.get("close_reason", "")]
    sl = [r for r in rows if "止損已觸發" in r.get("close_reason", "")]

    return {
        "samples": total,
        "wins": len(wins),
        "losses": len(losses),
        "tp3": len(tp3),
        "sl": len(sl),
        "win_rate": round(rate(len(wins), total), 2),
        "tp3_rate": round(rate(len(tp3), total), 2),
        "gross_profit": round(gp, 4),
        "gross_loss": round(-gl, 4),
        "net_pnl": round(net, 4),
        "profit_factor": round(pf, 4),
        "average_win": round(gp / len(wins), 4) if wins else 0,
        "average_loss": round((-gl) / len(losses), 4) if losses else 0,
    }

def group_stats(rows, key):
    groups = defaultdict(list)

    for r in rows:
        groups[r.get(key, "UNKNOWN")].append(r)

    result = {}

    for name, sample in groups.items():
        result[name] = calc_stats(sample)

    return result

def build_statistics(
    log_file=DEFAULT_LOG_FILE,
    start_time=DEFAULT_START_TIME,
):
    rows = load_closed_samples(log_file, start_time)

    result = {
        "log_file": log_file,
        "start_time": start_time,
        "all": calc_stats(rows),
        "by_side": group_stats(rows, "side"),
        "by_symbol": group_stats(rows, "symbol"),
        "by_day": {},
    }

    by_day = defaultdict(list)
    for r in rows:
        by_day[r.get("time", "")[:10]].append(r)

    for day, sample in sorted(by_day.items()):
        result["by_day"][day] = calc_stats(sample)

    return result

def save_statistics(
    output_file="statistics/statistics_v2_output.json",
    log_file=DEFAULT_LOG_FILE,
    start_time=DEFAULT_START_TIME,
):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    data = build_statistics(log_file, start_time)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return data

if __name__ == "__main__":
    data = save_statistics()

    print("===== Statistics Engine V2 =====")
    print("Start Time:", data["start_time"])
    print("Samples:", data["all"]["samples"])
    print("TP3:", data["all"]["tp3"])
    print("SL:", data["all"]["sl"])
    print("WinRate:", data["all"]["win_rate"])
    print("PF:", data["all"]["profit_factor"])
    print("NetPnL:", data["all"]["net_pnl"])
    print()
    print("Saved: statistics/statistics_v2_output.json")
