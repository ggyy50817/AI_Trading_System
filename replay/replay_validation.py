import pandas as pd
import os

LOG_FILE = "replay_trading_log.csv"

REPORT_DIR = "replay/report"
OUTPUT_DIR = "replay/output"

os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

if not os.path.exists(LOG_FILE):
    print("No replay log.")
    raise SystemExit

df = pd.read_csv(LOG_FILE)

if len(df) == 0:
    print("Empty replay log.")
    raise SystemExit

report = []

for side in ["LONG", "SHORT"]:

    sub = df[df["side"] == side]

    if len(sub) == 0:
        continue

    wins = sub[sub["pnl"] > 0]
    losses = sub[sub["pnl"] <= 0]

    gross_profit = wins["pnl"].sum()
    gross_loss = losses["pnl"].sum()

    pf = 0

    if gross_loss != 0:
        pf = abs(gross_profit / gross_loss)

    report.append({
        "Side": side,
        "Trades": len(sub),
        "Wins": len(wins),
        "Losses": len(losses),
        "WinRate": round(len(wins)/len(sub)*100,2),
        "NetPnL": round(sub["pnl"].sum(),6),
        "ProfitFactor": round(pf,4),
    })

result = pd.DataFrame(report)

print()
print("="*60)
print("Replay Validation Report V1")
print("="*60)
print(result)

result.to_csv(
    f"{OUTPUT_DIR}/validation_report.csv",
    index=False
)

with open(f"{REPORT_DIR}/Validation_Report.md","w") as f:

    f.write("# Replay Validation Report\n\n")

    f.write(result.to_markdown(index=False))

print()
print("Saved:")
print(" replay/output/validation_report.csv")
print(" replay/report/Validation_Report.md")
