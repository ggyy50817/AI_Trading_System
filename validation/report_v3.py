import json
from collections import Counter, defaultdict

from validation.parser import load_trading_log

OUTPUT_FILE = "validation_report.json"


def score_bucket(score):
    if score >= 90:
        return "90+"
    if score >= 85:
        return "85-89"
    if score >= 80:
        return "80-84"
    if score >= 75:
        return "75-79"
    if score >= 70:
        return "70-74"
    return "<70"


def profit_factor(gross_profit, gross_loss):
    if gross_loss <= 0:
        return 0.0
    return gross_profit / gross_loss


def build_report():
    rows = load_trading_log()

    full = [
        r for r in rows
        if r.get("action") == "FULL_CLOSE"
    ]

    valid = []
    invalid = []

    for row in full:
        market = str(row.get("market_regime", "UNKNOWN"))

        try:
            score = int(float(row.get("ai_score", 0)))
        except (TypeError, ValueError):
            invalid.append(row)
            continue

        # Old V3 samples without complete AI Context.
        if score == 0 and market == "UNKNOWN":
            invalid.append(row)
            continue

        valid.append(row)

    direction_counter = Counter()
    market_regime_counter = Counter()

    ai_score_counter = Counter()
    ai_score_tp_counter = Counter()
    ai_score_sl_counter = Counter()

    bucket_stats = defaultdict(lambda: {
        "samples": 0,
        "tp3": 0,
        "sl": 0,
        "wins": 0,
        "losses": 0,
        "gross_profit": 0.0,
        "gross_loss": 0.0,
        "net_pnl": 0.0,
    })

    for row in valid:
        direction = str(row.get("side", "UNKNOWN"))
        market = str(row.get("market_regime", "UNKNOWN"))
        score = int(float(row.get("ai_score", 0)))
        close_reason = str(row.get("close_reason", ""))

        try:
            pnl = float(row.get("pnl", 0) or 0)
        except (TypeError, ValueError):
            pnl = 0.0

        direction_counter[direction] += 1
        market_regime_counter[market] += 1

        ai_score_counter[score] += 1

        if "TP3" in close_reason:
            ai_score_tp_counter[score] += 1

        if "止損" in close_reason:
            ai_score_sl_counter[score] += 1

        bucket_name = score_bucket(score)
        stats = bucket_stats[bucket_name]

        stats["samples"] += 1
        stats["net_pnl"] += pnl

        if "TP3" in close_reason:
            stats["tp3"] += 1

        if "止損" in close_reason:
            stats["sl"] += 1

        if pnl > 0:
            stats["wins"] += 1
            stats["gross_profit"] += pnl
        elif pnl < 0:
            stats["losses"] += 1
            stats["gross_loss"] += abs(pnl)

    ai_score_report = {}

    for score in sorted(ai_score_counter.keys()):
        ai_score_report[str(score)] = {
            "samples": ai_score_counter[score],
            "tp": ai_score_tp_counter[score],
            "sl": ai_score_sl_counter[score],
        }

    bucket_report = {}

    bucket_order = [
        "<70",
        "70-74",
        "75-79",
        "80-84",
        "85-89",
        "90+",
    ]

    for name in bucket_order:
        if name not in bucket_stats:
            continue

        stats = bucket_stats[name]

        win_rate = (
            stats["wins"] / stats["samples"] * 100
            if stats["samples"]
            else 0.0
        )

        bucket_report[name] = {
            **stats,
            "win_rate": round(win_rate, 2),
            "profit_factor": round(
                profit_factor(
                    stats["gross_profit"],
                    stats["gross_loss"],
                ),
                4,
            ),
        }

    report = {
        "summary": {
            "rows": len(rows),
            "full_close": len(full),
            "valid_context": len(valid),
            "invalid_context": len(invalid),
        },
        "direction": dict(direction_counter),
        "market_regime": dict(market_regime_counter),
        "ai_score": ai_score_report,
        "ai_score_bucket": bucket_report,
    }

    return report


def save_report(report):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            report,
            f,
            indent=4,
            ensure_ascii=False,
        )


def main():
    report = build_report()
    save_report(report)

    print("=" * 60)
    print("Validation Report V3")
    print("=" * 60)

    summary = report["summary"]

    print(f"Rows: {summary['rows']}")
    print(f"Full Close: {summary['full_close']}")
    print(f"Valid Context: {summary['valid_context']}")
    print(f"Invalid Context: {summary['invalid_context']}")
    print(f"Direction: {report['direction']}")
    print(f"Market Regime: {report['market_regime']}")
    print(f"AI Score: {report['ai_score']}")

    print()
    print("===== AI Score Bucket =====")

    for name, stats in report["ai_score_bucket"].items():
        print(
            f"{name}: "
            f"Samples={stats['samples']} "
            f"TP3={stats['tp3']} "
            f"SL={stats['sl']} "
            f"WinRate={stats['win_rate']:.2f}% "
            f"PnL={stats['net_pnl']:.4f} "
            f"PF={stats['profit_factor']:.4f}"
        )

    print()
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
