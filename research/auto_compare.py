import json
import os

STAT_FILE = "statistics/statistics_v2_output.json"


def load_statistics():
    if not os.path.exists(STAT_FILE):
        raise FileNotFoundError(
            f"{STAT_FILE} 不存在，請先執行 python3 -m statistics.engine"
        )

    with open(STAT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def score_strategy(data):
    all_stat = data["all"]

    pf = all_stat["profit_factor"]
    wr = all_stat["win_rate"]
    pnl = all_stat["net_pnl"]

    score = (
        pf * 100
        + wr
        + pnl / 10
    )

    return round(score, 2)


def print_section(title, stat):

    print("=" * 60)
    print(title)
    print("=" * 60)

    print(f"Samples       : {stat['samples']}")
    print(f"TP3           : {stat['tp3']}")
    print(f"SL            : {stat['sl']}")
    print(f"WinRate       : {stat['win_rate']}%")
    print(f"ProfitFactor  : {stat['profit_factor']}")
    print(f"NetPnL        : {stat['net_pnl']}")
    print()


if __name__ == "__main__":

    data = load_statistics()

    print()
    print("=" * 60)
    print("Auto Compare V1")
    print("=" * 60)

    print_section(
        "ALL",
        data["all"]
    )

    print("LONG")

    for k, v in data["by_side"].get("LONG", {}).items():
        print(f"{k:15}: {v}")

    print()

    print("SHORT")

    for k, v in data["by_side"].get("SHORT", {}).items():
        print(f"{k:15}: {v}")

    print()

    print("=" * 60)
    print("Strategy Score")
    print("=" * 60)

    print(score_strategy(data))
