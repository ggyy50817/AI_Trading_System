import csv
import os
from collections import Counter, defaultdict

LOG_FILE = "trading_log_v2.csv"

EXPECTED_CONTEXT_FIELDS = [
    "ai_score",
    "funding_rate",
    "open_interest",
    "atr",
    "volume_spike",
    "ma20_position",
    "market_regime",
]

def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None

if not os.path.exists(LOG_FILE):
    print(f"❌ Missing {LOG_FILE}")
    raise SystemExit(1)

with open(LOG_FILE, newline="", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    headers = reader.fieldnames or []

print("===== Trading Log Audit V2 =====")
print(f"Rows: {len(rows)}")
print(f"Headers: {headers}")
print()

print("===== Existing / Missing Context Fields =====")
for field in EXPECTED_CONTEXT_FIELDS:
    if field in headers:
        values = [r.get(field, "") for r in rows]
        non_empty = sum(1 for v in values if str(v).strip() not in ("", "0", "0.0", "None", "UNKNOWN"))
        print(f"✅ {field}: exists, useful_values={non_empty}/{len(rows)}")
    else:
        print(f"❌ {field}: missing")
print()

print("===== Close Reason Counts =====")
reason_counter = Counter()
for r in rows:
    reason = r.get("close_reason", "")
    if "TP3" in reason:
        reason_counter["TP3"] += 1
    elif "止損" in reason:
        reason_counter["SL"] += 1
    elif "TP1" in reason:
        reason_counter["TP1"] += 1
    elif "TP2" in reason:
        reason_counter["TP2"] += 1
    else:
        reason_counter["OTHER"] += 1

for k, v in reason_counter.items():
    print(f"{k}: {v}")
print()

print("===== AI Score Quality =====")
if "ai_score" in headers:
    scores = [safe_float(r.get("ai_score", "")) for r in rows]
    scores = [s for s in scores if s is not None]
    zero_count = sum(1 for s in scores if s == 0)
    non_zero_count = sum(1 for s in scores if s != 0)
    print(f"ai_score numeric rows: {len(scores)}")
    print(f"ai_score zero: {zero_count}")
    print(f"ai_score non-zero: {non_zero_count}")
    if non_zero_count == 0:
        print("⚠️ AI Score 欄位存在，但目前沒有有效資料，Statistics V2 無法分析 AI Score。")
print()

print("===== Side Result Summary TP3/SL Only =====")
side_stats = defaultdict(lambda: {"TP3": 0, "SL": 0, "pnl": 0.0})
for r in rows:
    reason = r.get("close_reason", "")
    if "TP3" not in reason and "止損" not in reason:
        continue
    side = r.get("side", "UNKNOWN")
    pnl = safe_float(r.get("pnl", "")) or 0.0
    if "TP3" in reason:
        side_stats[side]["TP3"] += 1
    elif "止損" in reason:
        side_stats[side]["SL"] += 1
    side_stats[side]["pnl"] += pnl

for side, s in side_stats.items():
    total = s["TP3"] + s["SL"]
    rate = (s["TP3"] / total * 100) if total else 0
    print(f"{side}: samples={total}, TP3={s['TP3']}, SL={s['SL']}, TP3Rate={rate:.2f}%, PnL={s['pnl']:.4f}")
print()

print("===== Decision =====")
missing = [f for f in EXPECTED_CONTEXT_FIELDS if f not in headers]
ai_bad = "ai_score" in headers and all((safe_float(r.get("ai_score", "")) or 0) == 0 for r in rows)

if missing or ai_bad:
    print("目前不能直接做完整 Validation Statistics V2。")
    print("原因：交易紀錄缺少或沒有有效寫入關鍵上下文資料。")
    print("下一步應該是建立 Enhanced Trade Context Logging。")
else:
    print("資料欄位足夠，可以進入 Validation Statistics V2。")
