from penalty.penalty_loader import load_penalty

CONFIG_SOURCE = "research/config/penalty.json"


def apply_penalty(symbol, side, score):

    penalty_cfg = load_penalty()

    deduct = penalty_cfg.get(side, {}).get(symbol, 0)

    final_score = max(score - deduct, 0)

    if deduct > 0:
        reason = "Penalty Config"
    else:
        reason = None

    return {
        "symbol": symbol,
        "side": side,
        "original_score": score,
        "penalty": deduct,
        "final_score": final_score,
        "reason": reason,
        "config_source": CONFIG_SOURCE
    }
