import json
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
    market_regime_counter = Counter()
    ai_score_counter = Counter()

    for row in full:
        direction = row.get("side", "UNKNOWN")
        direction_counter[direction] += 1

        market = row.get("market_regime", "UNKNOWN")
        market_regime_counter[market] += 1

        score = row.get("ai_score")

        try:
            score = int(float(score))
            ai_score_counter[score] += 1
        except (TypeError, ValueError):
            continue

    ai_score_report = {}

    for score in sorted(ai_score_counter.keys()):
        ai_score_report[str(score)] = {
            "samples": ai_score_counter[score]
        }

    report = {
        "summary": {
            "rows": len(rows),
            "full_close": len(full)
        },
        "direction": dict(direction_counter),
        "market_regime": dict(market_regime_counter),
        "ai_score": ai_score_report
    }

    return report


def save_report(report):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)


def main():
    report = build_report()
    save_report(report)

    print("=" * 60)
    print("Validation Report V3")
    print("=" * 60)
    print(f"Rows: {report['summary']['rows']}")
    print(f"Full Close: {report['summary']['full_close']}")
    print(f"Direction: {report['direction']}")
    print(f"Market Regime: {report['market_regime']}")
    print(f"AI Score: {report['ai_score']}")
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()