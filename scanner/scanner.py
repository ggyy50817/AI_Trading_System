from logs.trade_logger import log_trade
from config.settings import BOT_MODE
from scanner.bingx_vst_api import safe_demo_order_test, has_existing_position
from logs.logger import log_message
from scanner.ai_score import calculate_ai_score, calculate_short_ai_score
from scanner.entry_filter import check_entry_permission
from telegram_utils.telegram_bot import send_telegram_message
from scanner.cooldown_engine import is_in_cooldown
from scanner.market_regime import get_market_regime

SHORT_MIN_SCORE = 90

def get_regime_thresholds(regime):
    if regime == "BULL":
        return 80, 95

    if regime == "BEAR":
        return 95, 90

    return 90, 95

WATCHLIST = [
    "BTC-USDT",
    "ETH-USDT",
    "SOL-USDT",
    "BNB-USDT",
    "XRP-USDT",
    "DOGE-USDT",
    "SUI-USDT",
    "LINK-USDT",
    "AVAX-USDT",

    "APT-USDT",
    "ARB-USDT",
    "OP-USDT",
    "INJ-USDT",
    "SEI-USDT",

    "FET-USDT",
    "RENDER-USDT",
    "TIA-USDT",
    "TON-USDT",
    "NEAR-USDT",

    "FIL-USDT",
    "ENA-USDT",
    "JUP-USDT",

    "WIF-USDT",
    "PEPE-USDT"
]


def run_scanner():

    current_regime = get_market_regime()
    long_min_score, short_min_score = get_regime_thresholds(current_regime)
    log_message(f"🌎 Market Regime V2: {current_regime} | LONG>={long_min_score} SHORT>={short_min_score}")

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

        can_long = ai_score >= long_min_score
        can_short = short_score >= short_min_score

        if can_long:
            log_message(f"✅ LONG AI Score {ai_score} >= {long_min_score}，允許做多")
        else:
            log_message(f"❌ LONG AI Score {ai_score} < {long_min_score}，禁止做多")

        if can_short:
            log_message(f"✅ SHORT AI Score {short_score} >= {short_min_score}，允許做空")
        else:
            log_message(f"❌ SHORT AI Score {short_score} < {short_min_score}，禁止做空")

        if can_short:

            if has_existing_position(symbol, "SHORT"):
                log_message(f"⏭️ {symbol} 已有 SHORT 持倉，跳過")
                continue
            if is_in_cooldown(symbol):
                log_message(f"🧊 {symbol} 冷卻中，跳過")
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

            if is_in_cooldown(symbol):
                log_message(f"🧊 {symbol} 冷卻中，跳過")
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
