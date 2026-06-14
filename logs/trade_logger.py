import csv
from datetime import datetime
import os


TRADE_LOG_FILE = "trading_log.csv"
CLOSE_LOG_FILE = "trading_log_v2.csv"


def log_trade(
    symbol,
    side,
    ai_score,
    bot_mode,
    result,
    entry_price=0,
    exit_price=0,
    pnl=0,
    pnl_percent=0
):

    file_exists = os.path.isfile(TRADE_LOG_FILE)

    with open(TRADE_LOG_FILE, "a", newline="", encoding="utf-8") as file:

        writer = csv.writer(file)

        if not file_exists:

            writer.writerow([
                "time",
                "symbol",
                "side",
                "entry_price",
                "exit_price",
                "pnl",
                "pnl_percent",
                "ai_score",
                "bot_mode",
                "result"
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            symbol,
            side,
            entry_price,
            exit_price,
            pnl,
            pnl_percent,
            ai_score,
            bot_mode,
            result
        ])


def log_close_trade(
    symbol,
    side,
    entry_price,
    exit_price,
    pnl,
    pnl_percent,
    ai_score=0,
    bot_mode="DEMO_TRADING",
    result="CLOSE",
    close_reason="UNKNOWN",
    action="UNKNOWN",
    close_percent=0
):

    file_exists = os.path.isfile(CLOSE_LOG_FILE)

    with open(CLOSE_LOG_FILE, "a", newline="", encoding="utf-8") as file:

        writer = csv.writer(file)

        if not file_exists:

            writer.writerow([
                "time",
                "symbol",
                "side",
                "entry_price",
                "exit_price",
                "pnl",
                "pnl_percent",
                "ai_score",
                "bot_mode",
                "result",
                "close_reason",
                "action",
                "close_percent"
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            symbol,
            side,
            entry_price,
            exit_price,
            pnl,
            pnl_percent,
            ai_score,
            bot_mode,
            result,
            close_reason,
            action,
            close_percent
        ])