import csv
import os

from validation_v2.config import START_TIME
from validation_v2.config import LOG_FILE


def load_closed_trades():

    if not os.path.exists(LOG_FILE):
        raise FileNotFoundError(LOG_FILE)

    rows = []

    with open(
        LOG_FILE,
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            if row["time"] < START_TIME:
                continue

            reason = row.get("close_reason", "")

            if (
                "TP3 已觸發" not in reason
                and
                "止損已觸發" not in reason
            ):
                continue

            rows.append(row)

    return rows


if __name__ == "__main__":

    trades = load_closed_trades()

    print("=" * 60)
    print("Validation Log Loader")
    print("=" * 60)

    print("Closed Trades:", len(trades))

    if trades:
        print()
        print("First Trade")
        print(trades[0])

        print()
        print("Last Trade")
        print(trades[-1])
