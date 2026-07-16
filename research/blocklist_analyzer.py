import csv
from collections import defaultdict

from research.blocklist_engine import save_blocklist

LOG_FILE="trading_log_v2.csv"
START_TIME="2026-06-23 03:29:00"

import json

with open("research/config/blocklist_rules.json","r") as f:
    rules=json.load(f)

MIN_SAMPLE=rules["min_samples"]
PF_LIMIT=rules["pf_limit"]
WIN_RATE_LIMIT=rules["win_rate_limit"]


def f(x):
    try:
        return float(x)
    except:
        return 0.0


rows=[]

with open(LOG_FILE,newline="",encoding="utf-8") as file:

    reader=csv.DictReader(file)

    for r in reader:

        if r["time"]<START_TIME:
            continue

        if (
            "TP3 已觸發" in r["close_reason"]
            or
            "止損已觸發" in r["close_reason"]
        ):
            rows.append(r)


group=defaultdict(list)

for r in rows:

    group[(r["side"],r["symbol"])].append(r)


result={
    "LONG":{},
    "SHORT":{}
}


print("="*70)
print("Blocklist Analyzer V2")
print("="*70)
print()


for (side,symbol),sample in sorted(group.items()):

    total=len(sample)

    wins=[
        r
        for r in sample
        if f(r["pnl"])>0
    ]

    losses=[
        r
        for r in sample
        if f(r["pnl"])<0
    ]

    gp=sum(f(r["pnl"]) for r in wins)
    gl=abs(sum(f(r["pnl"]) for r in losses))

    pf=0 if gl==0 else gp/gl

    wr=0 if total==0 else len(wins)/total*100

    if (
        total>=MIN_SAMPLE
        and
        pf<PF_LIMIT
        and
        wr<WIN_RATE_LIMIT
    ):

        result[side][symbol]={
            "samples":total,
            "pf":round(pf,4),
            "win_rate":round(wr,2)
        }

        print(
            f"{side:5}",
            f"{symbol:12}",
            f"S={total:3}",
            f"PF={pf:.4f}",
            f"WR={wr:.2f}%"
        )

save_blocklist(result)

print()
print("Saved:")
print("research/config/blocklist.json")
