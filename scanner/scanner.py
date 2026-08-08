from datetime import datetime

from viewlogs.trade_logger import log_trade
from viewlogs.trade_context import save_trade_context
from config.settings import BOT_MODE
from scanner.bingx_vst_api import safe_demo_order_test, has_existing_position
from viewlogs.logger import log_message
from scanner.ai_score import calculate_ai_score, calculate_short_ai_score, calculate_ai_context, calculate_short_ai_context
from scanner.entry_filter import check_entry_permission
from telegram_utils.telegram_bot import send_telegram_message
from scanner.cooldown_engine import is_in_cooldown
from scanner.market_regime import get_market_regime
from core.scanner_result import ScannerResult
from core.trading_decision_adapter import from_scanner
from decision_pipeline.pipeline import process_decision
from opportunity.factory import create_opportunity
from opportunity.logger import log_opportunity
from shadow.manager import create_shadow_trade
from shadow.logger import log_shadow_trade

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
    log_message(
    f"🌎 Regime={current_regime} "
    f"LONG>={long_min_score} "
    f"SHORT>={short_min_score}"
)

    log_message("🔍 Scanner is running...")

    for symbol in WATCHLIST:

        log_message(f"🔎 正在掃描：{symbol}")

        try:
            long_context = calculate_ai_context(symbol)
            short_context = calculate_short_ai_context(symbol)

            ai_score = long_context.get("score", 0)
            short_score = short_context.get("score", 0)

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

        opportunity_record= create_opportunity(
            symbol=symbol,
            market_regime=current_regime,
            long_score=ai_score,
            short_score=short_score,
            long_threshold=long_min_score,
            short_threshold=short_min_score,
            can_long=can_long,
            can_short=can_short,
            reason=None,
            context={
                "long": long_context,
                "short": short_context,
            },
        )

        log_opportunity(opportunity_record)

        shadow_trade = create_shadow_trade(opportunity_record)

        if shadow_trade is not None:
            log_shadow_trade(shadow_trade)
            log_message(
                f"👻 Shadow Trade: "
                f"{shadow_trade.symbol} "
                f"{shadow_trade.side} "
                f"AI={shadow_trade.ai_score} "
                f"Threshold={shadow_trade.threshold} "
                f"Entry={shadow_trade.entry_price}"
            )

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

            scanner_result = ScannerResult(
                symbol=symbol,
                side="SHORT",
                timestamp=datetime.now(),
                ai_score=short_score,
                threshold=short_min_score,
                market_regime=current_regime,
                context=short_context,
                order_result=order_result,
            )

            decision = from_scanner(scanner_result)

            process_decision(decision)

            saved_context = save_trade_context(
                symbol=symbol,
                side="SHORT",
                ai_score=short_score,
                bot_mode=BOT_MODE,
                extra={
                    **short_context,
                    "long_score": ai_score,
                    "short_score": short_score,
                    "threshold_long": long_min_score,
                    "threshold_short": short_min_score,
                    "market_regime": current_regime,
                }
            )
            log_message(f"✅ 已保存交易上下文：{symbol} SHORT AI={short_score} Regime={saved_context.get('market_regime')}")

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

            scanner_result = ScannerResult(
                symbol=symbol,
                side="LONG",
                timestamp=datetime.now(),
                ai_score=ai_score,
                threshold=long_min_score,
                market_regime=current_regime,
                context=long_context,
                order_result=order_result,
            )

            decision = from_scanner(scanner_result)

            process_decision(decision)

            saved_context = save_trade_context(
                symbol=symbol,
                side="LONG",
                ai_score=ai_score,
                bot_mode=BOT_MODE,
                extra={
                    **long_context,
                    "long_score": ai_score,
                    "short_score": short_score,
                    "threshold_long": long_min_score,
                    "threshold_short": short_min_score,
                    "market_regime": current_regime,
                }
            )
            log_message(f"✅ 已保存交易上下文：{symbol} LONG AI={ai_score} Regime={saved_context.get('market_regime')}")

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
