import csv

from replay_compare.config import START_TIME, LOG_FILE


def load_original():

    rows=[]

    with open(LOG_FILE,newline="",encoding="utf-8") as f:

        reader=csv.DictReader(f)

        for row in reader:

            if row["time"]<START_TIME:
                continue

            reason=row["close_reason"]

            if "TP3 已觸發" not in reason and \
               "止損已觸發" not in reason:
                continue

            rows.append(row)

    return rows


if __name__=="__main__":

    trades=load_original()

    print("="*70)
    print("Replay Original")
    print("="*70)

    print("Trades :",len(trades))

    if trades:

        print()
        print("First")
        print(
            trades[0]["time"],
            trades[0]["symbol"],
            trades[0]["side"],
            trades[0]["close_reason"]
        )

        print()

        print("Last")
        print(
            trades[-1]["time"],
            trades[-1]["symbol"],
            trades[-1]["side"],
            trades[-1]["close_reason"]
        )
