from scanner.bingx_api import (
    check_volume_spike,
    check_atr_condition,
    check_above_ma20,
)

def calculate_replay_ai_context(df):

    latest_close = float(df.iloc[-1]["Close"])
    latest_ma20 = float(df.iloc[-1]["MA20"])
    latest_atr = float(df.iloc[-1]["ATR"])
    latest_volume_ratio = float(df.iloc[-1]["VolumeRatio"])

    is_above = check_above_ma20(df)
    is_volume_spike = check_volume_spike(df)
    atr_status = check_atr_condition(df)

    score = 0

    if is_above:
        score += 40

    if is_volume_spike:
        score += 20

    if atr_status == "波動正常":
        score += 10

    return {
        "score": score,
        "latest_close": latest_close,
        "latest_ma20": latest_ma20,
        "atr": latest_atr,
        "volume_ratio": latest_volume_ratio,
        "volume_spike": is_volume_spike,
        "ma20_position": "ABOVE" if is_above else "BELOW",
    }
