import csv
from datetime import datetime
import os

from viewlogs.trade_context import get_trade_context, clear_trade_context


TRADE_LOG_FILE = "trading_log.csv"
CLOSE_LOG_FILE = "trading_log_v2.csv"
ENHANCED_CLOSE_LOG_FILE = "trading_log_v3.csv"


def _write_csv_row(file_path, header, row):
    file_exists = os.path.isfile(file_path)

    with open(file_path, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(header)

        writer.writerow(row)


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
    header = [
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
    ]

    row = [
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
    ]

    _write_csv_row(TRADE_LOG_FILE, header, row)


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
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    context = get_trade_context(symbol, side)

    if not ai_score or float(ai_score) == 0:
        ai_score = context.get("ai_score", 0)

    # Keep old V2 log unchanged for compatibility.
    old_header = [
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
    ]

    old_row = [
        now,
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
    ]

    _write_csv_row(CLOSE_LOG_FILE, old_header, old_row)

    # New V3 log with context for future Validation Statistics V2.
    enhanced_header = [
        "time",
        "symbol",
        "side",
        "entry_price",
        "exit_price",
        "pnl",
        "pnl_percent",
        "ai_score",
        "long_score",
        "short_score",
        "funding_rate",
        "open_interest",
        "atr",
        "volume_spike",
        "ma20_position",
        "market_regime",
        "threshold_long",
        "threshold_short",
        "bot_mode",
        "result",
        "close_reason",
        "action",
        "close_percent",
        "context_created_at"
    ]

    enhanced_row = [
        now,
        symbol,
        side,
        entry_price,
        exit_price,
        pnl,
        pnl_percent,
        ai_score,
        context.get("long_score", 0),
        context.get("short_score", 0),
        context.get("funding_rate", "UNKNOWN"),
        context.get("open_interest", "UNKNOWN"),
        context.get("atr", "UNKNOWN"),
        context.get("volume_spike", "UNKNOWN"),
        context.get("ma20_position", "UNKNOWN"),
        context.get("market_regime", "UNKNOWN"),
        context.get("threshold_long", "UNKNOWN"),
        context.get("threshold_short", "UNKNOWN"),
        bot_mode,
        result,
        close_reason,
        action,
        close_percent,
        context.get("created_at", "UNKNOWN")
    ]

    _write_csv_row(ENHANCED_CLOSE_LOG_FILE, enhanced_header, enhanced_row)

    if action == "FULL_CLOSE":
        clear_trade_context(symbol, side)
