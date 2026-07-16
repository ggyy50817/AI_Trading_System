from scanner.bingx_api import (
    check_volume_spike,
    check_atr_condition,
    check_above_ma20,
)

from replay.replay_ai_core import (
    calculate_long_score,
    calculate_short_score,
)

from penalty.penalty_engine import apply_penalty


def calculate_replay_ai_context(df, symbol="UNKNOWN"):

    latest_close = float(df.iloc[-1]["Close"])
    latest_ma20 = float(df.iloc[-1]["MA20"])
    latest_atr = float(df.iloc[-1]["ATR"])
    latest_volume_ratio = float(df.iloc[-1]["VolumeRatio"])

    is_above = check_above_ma20(df)
    is_below = latest_close < latest_ma20

    is_volume_spike = check_volume_spike(df)
    atr_status = check_atr_condition(df)

    long_score = calculate_long_score(
        is_above,
        is_volume_spike,
        atr_status,
    )

    short_score = calculate_short_score(
        is_below,
        is_volume_spike,
        atr_status,
    )

    long_result = apply_penalty(
        symbol,
        "LONG",
        long_score
    )

    short_result = apply_penalty(
        symbol,
        "SHORT",
        short_score
    )

    return {
        "long_score": long_result["final_score"],
        "short_score": short_result["final_score"],
        "long_penalty": long_result["penalty"],
        "short_penalty": short_result["penalty"],
        "latest_close": latest_close,
        "latest_ma20": latest_ma20,
        "atr": latest_atr,
        "volume_ratio": latest_volume_ratio,
        "volume_spike": is_volume_spike,
        "ma20_position": "ABOVE" if is_above else "BELOW",
    }
