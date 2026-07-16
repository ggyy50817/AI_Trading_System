from collections import defaultdict

from validation_v2.log_loader import load_closed_trades


def bucket(score):

    try:
        score = int(float(score))
    except:
        score = 0

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


rows = load_closed_trades()

stats = defaultdict(lambda: {
    "samples": 0,
    "tp3": 0,
    "sl": 0,
    "wins": 0,
    "losses": 0,
    "gross_profit": 0.0,
    "gross_loss": 0.0,
})

for r in rows:

    score = int(float(r.get("ai_score", 0)))

    # 忽略舊版 Log（ai_score=0）
    if score == 0:
        continue

    b = bucket(score)

    s = stats[b]

    s["samples"] += 1

    pnl = float(r["pnl"])

    if pnl > 0:
        s["wins"] += 1
        s["tp3"] += 1
        s["gross_profit"] += pnl
    else:
        s["losses"] += 1
        s["sl"] += 1
        s["gross_loss"] += abs(pnl)

print("=" * 70)
print("AI Score Bucket")
print("=" * 70)

order = [
    "<70",
    "70-74",
    "75-79",
    "80-84",
    "85-89",
    "90+"
]

for b in order:

    if b not in stats:
        continue

    s = stats[b]

    pf = (
        s["gross_profit"] / s["gross_loss"]
        if s["gross_loss"] > 0
        else 0
    )

    wr = (
        s["wins"] / s["samples"] * 100
        if s["samples"]
        else 0
    )

    print()

    print(f"Bucket : {b}")
    print(f"Samples: {s['samples']}")
    print(f"TP3    : {s['tp3']}")
    print(f"SL     : {s['sl']}")
    print(f"WinRate: {wr:.2f}%")
    print(f"PF     : {pf:.3f}")
