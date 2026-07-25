import json
from pathlib import Path
from collections import Counter

from validation.parser import load_trading_log

OUTPUT_FILE = "validation_report.json"


def build_report():
    rows = load_trading_log()

    full = [
        r for r in rows
        if r.get("action") == "FULL_CLOSE"
    ]

    direction_counter = Counter()

    for row in full:
        direction = row.get("side", "UNKNOWN")
        direction_counter[direction] += 1

    report = {
        "summary": {
            "rows": len(rows),
            "full_close": len(full)
        },
        "direction": dict(direction_counter),
        "market_regime": {},
        "ai_score": {}
    }

    return report


def save_report(report):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)


def main():
    report = build_report()
    save_report(report)

    print("=" * 60)
    print("Validation Report V2")
    print("=" * 60)
    print(f"Rows: {report['summary']['rows']}")
    print(f"Full Close: {report['summary']['full_close']}")
    print(f"Direction: {report['direction']}")
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()