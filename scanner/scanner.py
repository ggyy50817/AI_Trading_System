from logs.trade_logger import log_trade
from config.settings import BOT_MODE
from scanner.bingx_vst_api import safe_demo_order_test
from logs.logger import log_message
from scanner.ai_score import calculate_ai_score
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
    "PEPE-USDT",
    "LINK-USDT",
    "AVAX-USDT"
]

def run_scanner():

    log_message("🔍 Scanner is running...")

    for symbol in WATCHLIST:

        log_message(f"🔎 正在掃描：{symbol}")

        try:

            ai_score = calculate_ai_score(symbol)

        except Exception as e:

            log_message(f"❌ {symbol} 掃描失敗：{e}")
            continue

        log_message(f"🧠 {symbol} AI Score: {ai_score}")

        can_enter = check_entry_permission(ai_score)

        if can_enter:

            log_message(f"📌 {symbol} Signal added to watchlist")
            send_telegram_message(f"📌 發現高分訊號：{symbol}")

            order_result = safe_demo_order_test(symbol)

            #order_result = safe_demo_order_test()

            log_trade(
                symbol=symbol,
                side="LONG",
                ai_score=ai_score,
                bot_mode=BOT_MODE,
                result=str(order_result)
            )

            log_message(f"✅ {symbol} VST 模擬下單結果：{order_result}")

            if order_result and order_result.get("code") == 0:

                send_telegram_message(
                    f"""
📈 VST模擬開倉成功

幣種：{symbol}
方向：做多
AI分數：{ai_score}
模式：{BOT_MODE}
"""
                )

            else:

                send_telegram_message(
                    f"""
⛔ VST模擬開倉未執行

幣種：{symbol}
原因：已存在相同方向持倉或風控阻擋
AI分數：{ai_score}
模式：{BOT_MODE}
"""
                )

        else:

            log_message(f"⛔ {symbol} Signal rejected")
