import pandas as pd

df=pd.read_csv("replay_trading_log.csv")

print("="*60)
print("Replay Statistics V3")
print("="*60)

for side in ["LONG","SHORT"]:

    d=df[df.side==side]

    if len(d)==0:
        continue

    wins=d[d.pnl>0]
    loss=d[d.pnl<0]

    gp=wins.pnl.sum()
    gl=loss.pnl.sum()

    pf=0
    if gl!=0:
        pf=abs(gp/gl)

    print()
    print(side)
    print("-"*30)
    print("Trades :",len(d))
    print("Wins   :",len(wins))
    print("Loss   :",len(loss))
    print("WinRate: %.2f%%"%(len(wins)/len(d)*100))
    print("NetPnL :",round(d.pnl.sum(),6))
    print("PF     :",round(pf,4))

print()
print("="*60)
print("Close Reason")
print("="*60)
print(df.groupby(["side","reason"]).size())
