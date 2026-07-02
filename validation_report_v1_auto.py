import csv
from collections import defaultdict
from pathlib import Path

LOG_FILE = Path("trading_log_v3.csv")
OUT_DIR = Path("validation/report")
SUGGESTION_DIR = Path("validation/suggestion")
OUT_DIR.mkdir(parents=True, exist_ok=True)
SUGGESTION_DIR.mkdir(parents=True, exist_ok=True)

CLOSED_KEYWORDS = ["TP3 已觸發", "止損已觸發"]

def to_float(v, default=0.0):
    try:
        return float(v)
    except:
        return default

def is_closed(row):
    if len(row) < 24:
        return False
    reason = row[19]
    return any(k in reason for k in CLOSED_KEYWORDS)

def result_type(row):
    reason = row[19] if len(row) > 19 else ""
    if "TP3 已觸發" in reason:
        return "TP3"
    if "止損已觸發" in reason:
        return "SL"
    return "OTHER"

def add_stat(bucket, row):
    pnl = to_float(row[5])
    res = result_type(row)
    bucket["count"] += 1
    bucket["pnl"] += pnl
    if res == "TP3":
        bucket["tp3"] += 1
        bucket["profit"] += max(pnl, 0)
    elif res == "SL":
        bucket["sl"] += 1
        bucket["loss"] += min(pnl, 0)

def summarize(name, data):
    lines = []
    lines.append(f"===== {name} =====")
    ranked = sorted(data.items(), key=lambda x: x[1]["pnl"], reverse=True)
    for key, s in ranked:
        count = s["count"]
        tp3 = s["tp3"]
        sl = s["sl"]
        pnl = s["pnl"]
        win_rate = tp3 / count * 100 if count else 0
        pf = s["profit"] / abs(s["loss"]) if s["loss"] < 0 else 999
        lines.append(f"{key}: count={count}, TP3={tp3}, SL={sl}, win_rate={win_rate:.2f}%, pnl={pnl:.4f}, PF={pf:.4f}")
    lines.append("")
    return lines

def main():
    if not LOG_FILE.exists():
        print("找不到 trading_log_v3.csv")
        return

    rows = []
    with LOG_FILE.open("r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        for r in reader:
            if is_closed(r):
                rows.append(r)

    total = len(rows)
    if total == 0:
        print("沒有 TP3/SL 有效樣本")
        return

    total_pnl = sum(to_float(r[5]) for r in rows)
    tp3_count = sum(1 for r in rows if result_type(r) == "TP3")
    sl_count = sum(1 for r in rows if result_type(r) == "SL")
    gross_profit = sum(max(to_float(r[5]), 0) for r in rows)
    gross_loss = sum(min(to_float(r[5]), 0) for r in rows)
    pf = gross_profit / abs(gross_loss) if gross_loss < 0 else 999

    by_side = defaultdict(lambda: {"count":0,"tp3":0,"sl":0,"pnl":0.0,"profit":0.0,"loss":0.0})
    by_symbol = defaultdict(lambda: {"count":0,"tp3":0,"sl":0,"pnl":0.0,"profit":0.0,"loss":0.0})
    by_regime = defaultdict(lambda: {"count":0,"tp3":0,"sl":0,"pnl":0.0,"profit":0.0,"loss":0.0})
    by_score = defaultdict(lambda: {"count":0,"tp3":0,"sl":0,"pnl":0.0,"profit":0.0,"loss":0.0})

    for r in rows:
        side = r[2]
        symbol = r[1]
        regime = r[14] if len(r) > 14 else "UNKNOWN"

        long_score = r[15] if len(r) > 15 else "UNKNOWN"
        short_score = r[16] if len(r) > 16 else "UNKNOWN"
        score = short_score if side == "SHORT" else long_score

        try:
            score_bucket = f"{int(float(score)//10*10)}-{int(float(score)//10*10+9)}"
        except:
            score_bucket = "UNKNOWN"

        add_stat(by_side[side], r)
        add_stat(by_symbol[symbol], r)
        add_stat(by_regime[regime], r)
        add_stat(by_score[score_bucket], r)

    lines = []
    lines.append("===== Validation Report V1 Auto =====")
    lines.append(f"Valid Closed Samples TP3/SL: {total}")
    lines.append(f"TP3 Count: {tp3_count}")
    lines.append(f"SL Count: {sl_count}")
    lines.append(f"TP3 Rate: {tp3_count/total*100:.2f}%")
    lines.append(f"Closed PnL: {total_pnl:.4f}")
    lines.append(f"Gross Profit: {gross_profit:.4f}")
    lines.append(f"Gross Loss: {gross_loss:.4f}")
    lines.append(f"Profit Factor: {pf:.4f}")
    lines.append("")

    lines += summarize("LONG vs SHORT", by_side)
    lines += summarize("Symbol Ranking", by_symbol)
    lines += summarize("Market Regime", by_regime)
    lines += summarize("AI Score Bucket", by_score)

    report = "\n".join(lines)
    print(report)

    report_file = OUT_DIR / "validation_report_v1_auto.txt"
    report_file.write_text(report, encoding="utf-8")
    print(f"已輸出: {report_file}")

    blocklist_file = SUGGESTION_DIR / "blocklist_candidate.csv"
    penalty_file = SUGGESTION_DIR / "penalty_candidate.csv"

    with blocklist_file.open("w", encoding="utf-8") as f:
        f.write("type,key,count,tp3,sl,pnl,pf,suggestion\n")
        for symbol, s in sorted(by_symbol.items(), key=lambda x: x[1]["pnl"]):
            if s["count"] >= 10:
                pf_s = s["profit"] / abs(s["loss"]) if s["loss"] < 0 else 999
                if s["pnl"] < 0 and pf_s < 0.7:
                    f.write(f"SYMBOL,{symbol},{s['count']},{s['tp3']},{s['sl']},{s['pnl']:.4f},{pf_s:.4f},REVIEW_BLOCKLIST\n")

    with penalty_file.open("w", encoding="utf-8") as f:
        f.write("type,key,count,tp3,sl,pnl,pf,suggestion\n")
        for bucket, s in sorted(by_score.items(), key=lambda x: x[1]["pnl"]):
            if s["count"] >= 10:
                pf_s = s["profit"] / abs(s["loss"]) if s["loss"] < 0 else 999
                if s["pnl"] < 0 and pf_s < 1:
                    f.write(f"AI_SCORE_BUCKET,{bucket},{s['count']},{s['tp3']},{s['sl']},{s['pnl']:.4f},{pf_s:.4f},REVIEW_PENALTY_THRESHOLD\n")

    print(f"已輸出: {blocklist_file}")
    print(f"已輸出: {penalty_file}")

if __name__ == "__main__":
    main()
