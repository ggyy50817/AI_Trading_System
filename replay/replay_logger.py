import csv
import os
from datetime import datetime
from replay.replay_config import REPLAY_LOG_FILE

HEADER = [
    "time","symbol","side","entry_price","exit_price",
    "pnl","pnl_percent","ai_score","market_regime",
    "close_reason","action"
]

def log_replay_trade(row):
    exists = os.path.exists(REPLAY_LOG_FILE)
    with open(REPLAY_LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        if not exists:
            writer.writeheader()
        writer.writerow(row)
