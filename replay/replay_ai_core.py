def calculate_long_score(
    is_above,
    is_volume_spike,
    atr_status,
    funding_status=None,
    oi_status=None,
    market_regime=None,
):

    score = 0

    if is_above:
        score += 40

    if is_volume_spike:
        score += 20

    if funding_status == "偏多訊號":
        score += 20

    if oi_status == "資料正常":
        score += 10

    if atr_status == "波動正常":
        score += 10

    if market_regime == "BULL":
        score += 10

    return score


def calculate_short_score(
    is_below,
    is_volume_spike,
    atr_status,
    funding_status=None,
    oi_status=None,
    market_regime=None,
):

    score = 0

    if is_below:
        score += 40

    if is_volume_spike:
        score += 20

    if funding_status == "偏空訊號":
        score += 20

    if oi_status == "資料正常":
        score += 10

    if atr_status == "波動正常":
        score += 10

    if market_regime == "BEAR":
        score += 10

    return score
