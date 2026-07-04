import pandas as pd

df=pd.read_csv("trading_log_v3.csv")

full=df[df.action=="FULL_CLOSE"].copy()

print("="*70)
print("Validation Report V2")
print("="*70)

keys=[
"market_regime",
"ai_score",
"funding_rate",
"volume_spike",
"ma20_position",
"symbol"
]

for k in keys:
    print()
    print("="*70)
    print(k)
    print("="*70)

    g=full.groupby(k).agg(
        Samples=("pnl","count"),
        TotalPnL=("pnl","sum"),
        AvgPnL=("pnl","mean"),
        WinRate=("pnl",lambda x:(x>0).mean()*100)
    )

    print(g.sort_values("TotalPnL"))

print()
print("="*70)
print("Worst 20 Trades")
print("="*70)

cols=[
"time",
"symbol",
"ai_score",
"market_regime",
"funding_rate",
"volume_spike",
"ma20_position",
"pnl"
]

print(full.sort_values("pnl").head(20)[cols])

print()
print("="*70)
print("Best 20 Trades")
print("="*70)

print(full.sort_values("pnl",ascending=False).head(20)[cols])
