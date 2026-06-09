from logs.trade_logger import log_trade
from config.settings import BOT_MODE
from scanner.bingx_vst_api import safe_demo_order_test, has_existing_position
from logs.logger import log_message
from scanner.ai_score import calculate_ai_score, calculate_short_ai_score
from scanner.entry_filter import check_entry_permission
from telegram_utils.telegram_bot import send_telegram_message

WATCHLIST = [
    "BTC-USDT",
    "ETH-USDT",
    "SOL-USDT",
    "BNB-USDT",
    "XRP-USDT",
    "DOGE-USDT",
    "SUI-USDT",
    # "PEPE-USDT",
    "LINK-USDT",
    "AVAX-USDT"
]


def run_scanner():

    log_message("🔍 Scanner is running...")

    for symbol in WATCHLIST:

        log_message(f"🔎 正在掃描：{symbol}")

        try:
            ai_score = calculate_ai_score(symbol)
            short_score = calculate_short_ai_score(symbol)

        except Exception as e:
            log_message(f"❌ {symbol} 掃描失敗：{e}")
            continue

        log_message(f"🧠 {symbol} LONG AI Score: {ai_score}")
        log_message(f"🧠 {symbol} SHORT AI Score: {short_score}")

        can_long = check_entry_permission(ai_score)
        can_short = check_entry_permission(short_score)

        if can_short:

            if has_existing_position(symbol, "SHORT"):
                log_message(f"⏭️ {symbol} 已有 SHORT 持倉，跳過")
                continue

            log_message(f"📌 {symbol} SHORT Signal added")
            send_telegram_message(f"📌 發現高分做空訊號：{symbol}")

            order_result = safe_demo_order_test(
                symbol,
                direction="SHORT"
            )

            log_trade(
                symbol=symbol,
                side="SHORT",
                ai_score=short_score,
                bot_mode=BOT_MODE,
                result=str(order_result)
            )

            log_message(f"✅ {symbol} SHORT VST結果：{order_result}")

            continue

        if can_long:

            if has_existing_position(symbol, "LONG"):
                log_message(f"⏭️ {symbol} 已有 LONG 持倉，跳過")
                continue

            log_message(f"📌 {symbol} LONG Signal added")
            send_telegram_message(f"📌 發現高分做多訊號：{symbol}")

            order_result = safe_demo_order_test(
                symbol,
                direction="LONG"
            )

            log_trade(
                symbol=symbol,
                side="LONG",
                ai_score=ai_score,
                bot_mode=BOT_MODE,
                result=str(order_result)
            )

            log_message(f"✅ {symbol} LONG VST結果：{order_result}")

            continue

        log_message(f"⛔ {symbol} LONG / SHORT Signal rejected")