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
        # Direction
        direction = row.get("side", "UNKNOWN")
        direction_counter[direction] += 1

        # Market Regime
        market = row.get("market_regime", "UNKNOWN")
        market_regime_counter[market] += 1

        # AI Score Bucket
        score = row.get("ai_score")

        try:
            score = int(float(score))
        except (TypeError, ValueError):
            continue

        if 70 <= score <= 74:
            bucket = "70~74"
        elif 75 <= score <= 79:
            bucket = "75~79"
        elif 80 <= score <= 84:
            bucket = "80~84"
        elif 85 <= score <= 89:
            bucket = "85~89"
        elif score >= 90:
            bucket = "90+"
        else:
            continue

        ai_score_counter[bucket] += 1

    report = {
        "summary": {
            "rows": len(rows),
            "full_close": len(full)
        },
        "direction": dict(direction_counter),
        "market_regime": dict(market_regime_counter),
        "ai_score": dict(ai_score_counter)
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
    print(f"Market Regime: {report['market_regime']}")
    print(f"AI Score: {report['ai_score']}")
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()