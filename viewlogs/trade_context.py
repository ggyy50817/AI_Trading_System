import json
import os
from datetime import datetime

STATE_FILE = "trade_context_state.json"

DEFAULT_CONTEXT = {
    "ai_score": 0,
    "long_score": 0,
    "short_score": 0,
    "funding_rate": "UNKNOWN",
    "open_interest": "UNKNOWN",
    "atr": "UNKNOWN",
    "volume_spike": "UNKNOWN",
    "ma20_position": "UNKNOWN",
    "market_regime": "UNKNOWN",
    "threshold_long": "UNKNOWN",
    "threshold_short": "UNKNOWN",
    "created_at": "UNKNOWN",
}

def _key(symbol, side):
    return f"{symbol}_{side}"

def _load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def get_current_market_regime_safe():
    try:
        from scanner.market_regime import get_market_regime
        return get_market_regime()
    except Exception:
        pass

    try:
        from scanner.market_regime import detect_market_regime
        return detect_market_regime()
    except Exception:
        pass

    try:
        from terminal.regime import get_market_regime
        return get_market_regime()
    except Exception:
        pass

    return "UNKNOWN"

def save_trade_context(symbol, side, ai_score=0, bot_mode="UNKNOWN", extra=None):
    state = _load_state()
    context = dict(DEFAULT_CONTEXT)
    context.update({
        "symbol": symbol,
        "side": side,
        "ai_score": ai_score,
        "bot_mode": bot_mode,
        "market_regime": get_current_market_regime_safe(),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

    print("="*80)
    print("DEBUG EXTRA")
    print(extra)
    print("="*80)

    if extra and isinstance(extra, dict):
        context.update(extra)

    state[_key(symbol, side)] = context
    _save_state(state)
    return context

def get_trade_context(symbol, side):
    state = _load_state()
    context = dict(DEFAULT_CONTEXT)
    saved = state.get(_key(symbol, side), {})
    if isinstance(saved, dict):
        context.update(saved)
    return context

def clear_trade_context(symbol, side):
    state = _load_state()
    key = _key(symbol, side)
    if key in state:
        del state[key]
        _save_state(state)
