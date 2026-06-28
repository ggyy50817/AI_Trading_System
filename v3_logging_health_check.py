import os
import csv
import json

print("===== V3 Logging Health Check =====")

files = [
    "trade_context_state.json",
    "trading_log_v3.csv",
    "trading_log_v2.csv",
]

for f in files:
    if os.path.exists(f):
        print(f"✅ {f}: exists, size={os.path.getsize(f)} bytes")
    else:
        print(f"⚠️ {f}: not created yet")

print()

if os.path.exists("trade_context_state.json"):
    try:
        with open("trade_context_state.json", "r", encoding="utf-8") as fp:
            data = json.load(fp)
        print("===== Context State =====")
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"❌ Cannot read context state: {e}")

print()

if os.path.exists("trading_log_v3.csv"):
    with open("trading_log_v3.csv", newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        print("===== V3 CSV =====")
        print(f"Rows: {len(rows)}")
        print(f"Headers: {reader.fieldnames}")
        print("Last 5 rows:")
        for r in rows[-5:]:
            print(r)
else:
    print("===== V3 CSV =====")
    print("尚未產生。原因通常是：尚未有新平倉事件。")

print()
print("===== Decision =====")
if not os.path.exists("trade_context_state.json"):
    print("目前尚未有新進場 context。若 tmux 沒有 Signal added，這是正常。")
elif not os.path.exists("trading_log_v3.csv"):
    print("已有 context，但尚未有新平倉。等待 TP/SL/TP1/TP2/TP3。")
else:
    print("V3 logging 已開始產生資料，可以進入樣本收集階段。")
