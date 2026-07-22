"""Decision Pipeline standalone test.

Purpose:
    Verify that TradingDecision -> process_decision() -> Consumer works
    without running the whole trading bot.
"""

from datetime import datetime

from core.trading_decision import TradingDecision
from decision_pipeline.pipeline import process_decision


fake_decision: TradingDecision = {
    "timestamp": datetime.now().isoformat(),
    "symbol": "BTC-USDT",
    "side": "LONG",
    "source": "TEST",
    "price": 100000.0,
    "long_score": 88,
    "short_score": None,
    "ai_score": 88,
    "market_regime": "BULL",
    "signal_ok": True,
    "blocked": False,
    "block_reason": None,
    "order_submitted": True,
    "order_success": True,
    "order_result": None,
    "reason": "Pipeline Test",
    "skip_reason": None,
}

process_decision(fake_decision)

print("\n✅ Decision Pipeline test finished.")