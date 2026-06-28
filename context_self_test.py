from viewlogs.trade_context import save_trade_context, get_trade_context, clear_trade_context

symbol = "TEST-USDT"
side = "LONG"

print("===== Context Self Test =====")

ctx = save_trade_context(
    symbol=symbol,
    side=side,
    ai_score=99,
    bot_mode="SELF_TEST",
    extra={
        "long_score": 99,
        "short_score": 11,
        "threshold_long": 90,
        "threshold_short": 95,
        "funding_rate": "SELF_TEST",
        "open_interest": "SELF_TEST",
        "atr": "SELF_TEST",
        "volume_spike": "SELF_TEST",
        "ma20_position": "SELF_TEST",
        "market_regime": "SELF_TEST",
    }
)

print("Saved:")
print(ctx)

loaded = get_trade_context(symbol, side)
print("Loaded:")
print(loaded)

assert loaded["ai_score"] == 99
assert loaded["long_score"] == 99
assert loaded["short_score"] == 11

clear_trade_context(symbol, side)
loaded_after_clear = get_trade_context(symbol, side)

print("After clear:")
print(loaded_after_clear)

print("✅ Context self test passed")
