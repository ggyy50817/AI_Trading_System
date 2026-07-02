import csv
from collections import Counter, defaultdict
from pathlib import Path

LOG_FILE = Path("trading_log_v3.csv")
OUT_DIR = Path("validation/context")
OUT_DIR.mkdir(parents=True, exist_ok=True)

UNKNOWN_VALUES = {"UNKNOWN", "", "None", "nan", "NaN", None}

def is_unknown(v):
    return v is None or str(v).strip() in UNKNOWN_VALUES

def main():
    if not LOG_FILE.exists():
        print("找不到 trading_log_v3.csv")
        return

    rows = []
    with LOG_FILE.open("r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        for r in reader:
            if len(r) >= 24:
                rows.append(r)

    total = len(rows)
    if total == 0:
        print("沒有可分析資料")
        return

    fields = {
        "volume_spike": 9,
        "funding_rate": 10,
        "open_interest": 11,
        "atr": 12,
        "ma20": 13,
        "market_regime": 14,
        "long_score": 15,
        "short_score": 16,
        "entry_time": 23,
    }

    report_lines = []
    report_lines.append("===== Trading Log V3 Context Quality =====")
    report_lines.append(f"Total Rows: {total}")
    report_lines.append("")

    for name, idx in fields.items():
        unknown_count = sum(1 for r in rows if len(r) <= idx or is_unknown(r[idx]))
        known_count = total - unknown_count
        known_rate = known_count / total * 100
        unknown_rate = unknown_count / total * 100
        report_lines.append(f"{name}: known={known_count} ({known_rate:.2f}%), unknown={unknown_count} ({unknown_rate:.2f}%)")

    report_lines.append("")
    report_lines.append("===== By Action =====")

    action_counter = Counter()
    for r in rows:
        action = r[20] if len(r) > 20 else "UNKNOWN"
        action_counter[action] += 1

    for k, v in action_counter.most_common():
        report_lines.append(f"{k}: {v}")

    report_lines.append("")
    report_lines.append("===== By Side =====")

    side_counter = Counter()
    for r in rows:
        side = r[2] if len(r) > 2 else "UNKNOWN"
        side_counter[side] += 1

    for k, v in side_counter.most_common():
        report_lines.append(f"{k}: {v}")

    report = "\n".join(report_lines)

    print(report)

    out_file = OUT_DIR / "v3_context_quality_report.txt"
    out_file.write_text(report, encoding="utf-8")
    print("")
    print(f"已輸出: {out_file}")

if __name__ == "__main__":
    main()
