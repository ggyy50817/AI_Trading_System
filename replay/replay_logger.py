import csv
import os
from datetime import datetime

FILE="replay_trading_log.csv"

HEADER=[
"time",
"symbol",
"side",
"entry",
"exit",
"reason",
"pnl"
]

def save_trade(symbol,side,entry,exit_price,reason):

    if side=="LONG":
        pnl=exit_price-entry
    else:
        pnl=entry-exit_price

    write_header=not os.path.exists(FILE)

    with open(FILE,"a",newline="",encoding="utf-8") as f:

        writer=csv.writer(f)

        if write_header:
            writer.writerow(HEADER)

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            symbol,
            side,
            round(entry,6),
            round(exit_price,6),
            reason,
            round(pnl,6)
        ])
