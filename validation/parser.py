import csv
from pathlib import Path

DEFAULT_LOG = Path(__file__).resolve().parent.parent / "trading_log_v3.csv"


def load_trading_log(path=DEFAULT_LOG):
    path = Path(path)

    if not path.exists():
        print(f"找不到：{path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    return rows


if __name__ == "__main__":
    rows = load_trading_log()

    print("=" * 60)
    print(f"Rows : {len(rows)}")

    if rows:
        print("=" * 60)
        print("Header:")
        print(list(rows[0].keys()))

        print("=" * 60)
        print("First Row:")
        for k, v in rows[0].items():
            print(f"{k}: {v}")