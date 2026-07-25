import json
from pathlib import Path

from validation.parser import load_trading_log

OUTPUT_FILE = "validation_report.json"


def build_report():
    rows = load_trading_log()

    report = {
        "summary": {
            "rows": len(rows)
        },
        "direction": {},
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
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()