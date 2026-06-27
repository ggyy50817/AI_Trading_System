import csv
import os
from collections import defaultdict

TRADE_LOG_FILE = "trading_log_v2.csv"
START_TIME = "2026-06-14 17:18:00"


def safe_float(value, default=0.0):
    try:
        return float(value)
    except:
        return default


def is_success(row):
    return "'code': 0" in row.get("result", "") or '"code": 0' in row.get("result", "")


def main():
    if not os.path.isfile(TRADE_LOG_FILE):
        print(f"找不到 {TRADE_LOG_FILE}")
        return

    rows = []
    with open(TRADE_LOG_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("time", "") >= START_TIME:
                rows.append(row)

    total_events = len(rows)
    success_events = [r for r in rows if is_success(r)]
    failed_events = [r for r in rows if not is_success(r)]

    total_pnl = sum(safe_float(r.get("pnl", 0)) for r in success_events)

    side_pnl = defaultdict(float)
    side_count = defaultdict(int)

    symbol_pnl = defaultdict(float)
    symbol_count = defaultdict(int)

    tp1 = tp2 = tp3 = sl = 0
    win = loss = 0
    win_pnl = 0.0
    loss_pnl = 0.0

    score_pnl = defaultdict(float)
    score_count = defaultdict(int)

    for r in success_events:
        pnl = safe_float(r.get("pnl", 0))
        side = r.get("side", "UNKNOWN")
        symbol = r.get("symbol", "UNKNOWN")
        close_reason = r.get("close_reason", "")
        score = r.get("ai_score", "UNKNOWN")

        side_pnl[side] += pnl
        side_count[side] += 1

        symbol_pnl[symbol] += pnl
        symbol_count[symbol] += 1

        score_pnl[score] += pnl
        score_count[score] += 1

        if "TP1" in close_reason:
            tp1 += 1
        if "TP2" in close_reason:
            tp2 += 1
        if "TP3" in close_reason:
            tp3 += 1
        if "止損" in close_reason:
            sl += 1

        if pnl > 0:
            win += 1
            win_pnl += pnl
        elif pnl < 0:
            loss += 1
            loss_pnl += pnl

    win_rate = (win / len(success_events) * 100) if success_events else 0
    avg_win = (win_pnl / win) if win else 0
    avg_loss = (loss_pnl / loss) if loss else 0

    print("📊 Trading Statistics V1.1")
    print(f"Start Time: {START_TIME}")
    print("=" * 40)
    print(f"Total Events: {total_events}")
    print(f"Success Events: {len(success_events)}")
    print(f"Failed Events: {len(failed_events)}")
    print(f"Gross PnL: {total_pnl:.4f}")
    print(f"Win: {win}")
    print(f"Loss: {loss}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Average Win: {avg_win:.4f}")
    print(f"Average Loss: {avg_loss:.4f}")
    print("=" * 40)
    print(f"TP1: {tp1}")
    print(f"TP2: {tp2}")
    print(f"TP3: {tp3}")
    print(f"SL : {sl}")
    print("=" * 40)

    print("Side PnL:")
    for side in sorted(side_pnl.keys()):
        print(f"{side}: count={side_count[side]}, pnl={side_pnl[side]:.4f}")

    print("=" * 40)
    print("Top 10 Symbol PnL:")
    for symbol, pnl in sorted(symbol_pnl.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{symbol}: count={symbol_count[symbol]}, pnl={pnl:.4f}")

    print("=" * 40)
    print("Bottom 10 Symbol PnL:")
    for symbol, pnl in sorted(symbol_pnl.items(), key=lambda x: x[1])[:10]:
        print(f"{symbol}: count={symbol_count[symbol]}, pnl={pnl:.4f}")

    print("=" * 40)
    print("AI Score PnL:")
    for score in sorted(score_pnl.keys()):
        print(f"Score {score}: count={score_count[score]}, pnl={score_pnl[score]:.4f}")

    print("=" * 40)
    print("Note: Gross PnL 尚未扣除手續費與 Funding Fee")


if __name__ == "__main__":
    main()
