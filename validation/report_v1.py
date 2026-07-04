import pandas as pd

df = pd.read_csv("trading_log_v3.csv")

print("="*60)
print("Validation Report V1")
print("="*60)

closed = df[df["action"]=="FULL_CLOSE"]

print("\n總樣本：",len(closed))

print("\n=== Market Regime ===")
print(closed.groupby("market_regime")["pnl"].agg(["count","sum","mean"]))

print("\n=== Symbol ===")
print(closed.groupby("symbol")["pnl"].agg(["count","sum","mean"]).sort_values("sum"))

print("\n=== AI Score ===")
print(closed.groupby("ai_score")["pnl"].agg(["count","sum","mean"]))

print("\n=== Volume Spike ===")
print(closed.groupby("volume_spike")["pnl"].agg(["count","sum","mean"]))

print("\n=== MA20 ===")
print(closed.groupby("ma20_position")["pnl"].agg(["count","sum","mean"]))

print("\n=== Funding ===")
print(closed.groupby("funding_rate")["pnl"].agg(["count","sum","mean"]))

print("\n=== Top10 Loss ===")
print(
closed.sort_values("pnl").head(10)[
[
"time",
"symbol",
"side",
"ai_score",
"market_regime",
"funding_rate",
"volume_spike",
"ma20_position",
"pnl"
]
]
)

print("\n=== Top10 Profit ===")
print(
closed.sort_values("pnl",ascending=False).head(10)[
[
"time",
"symbol",
"side",
"ai_score",
"market_regime",
"funding_rate",
"volume_spike",
"ma20_position",
"pnl"
]
]
)
