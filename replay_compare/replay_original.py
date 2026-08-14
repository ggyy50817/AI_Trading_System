import csv

from replay_compare.config import START_TIME, LOG_FILE


def load_original():
    rows = []

    with open(
        LOG_FILE,
        newline="",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            if row.get("time", "") < START_TIME:
                continue

            if row.get("action") != "FULL_CLOSE":
                continue

            reason = row.get("close_reason", "")

            if (
                "TP3 已觸發" not in reason
                and "止損已觸發" not in reason
            ):
                continue

            market = str(
                row.get(
                    "market_regime",
                    "UNKNOWN"
                )
            )

            try:
                score = int(
                    float(
                        row.get(
                            "ai_score",
                            0
                        )
                    )
                )
            except (TypeError, ValueError):
                continue

            # Exclude legacy rows without valid AI Context.
            if score == 0 and market == "UNKNOWN":
                continue

            rows.append(row)

    return rows


if __name__ == "__main__":

    trades = load_original()

    print("=" * 70)
    print("Replay Original V3")
    print("=" * 70)

    print("Valid Context Trades:", len(trades))

    if trades:

        print()
        print("First")
        print(
            trades[0].get("time"),
            trades[0].get("symbol"),
            trades[0].get("side"),
            trades[0].get("ai_score"),
            trades[0].get("market_regime"),
            trades[0].get("close_reason"),
        )

        print()
        print("Last")
        print(
            trades[-1].get("time"),
            trades[-1].get("symbol"),
            trades[-1].get("side"),
            trades[-1].get("ai_score"),
            trades[-1].get("market_regime"),
            trades[-1].get("close_reason"),
        )
