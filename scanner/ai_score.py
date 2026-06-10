from scanner.market_regime import get_market_regime

from scanner.bingx_api import (
    get_klines,
    klines_to_dataframe,
    check_above_ma20,
    check_volume_spike,
    check_atr_condition,
    get_funding_rate,
    parse_funding_rate,
    check_funding_condition,
    get_open_interest,
    parse_open_interest,
    check_oi_condition,
    calculate_ai_score as calculate_real_ai_score
)

def calculate_ai_score(symbol="BTC-USDT"):

    klines = get_klines(symbol)

    df = klines_to_dataframe(klines)

    is_above = check_above_ma20(df)

    is_volume_spike = check_volume_spike(df)

    atr_status = check_atr_condition(df)

    funding = get_funding_rate(symbol)

    funding_percent = parse_funding_rate(funding)

    funding_status = check_funding_condition(funding_percent)

    oi = get_open_interest(symbol)

    open_interest = parse_open_interest(oi)

    oi_status = check_oi_condition(open_interest)

    print("===== AI Score Debug =====")
    print(f"MA20 是否站上：{is_above}")
    print(f"是否爆量：{is_volume_spike}")
    print(f"ATR 狀態：{atr_status}")
    print(f"Funding 狀態：{funding_status}")
    print(f"OI 狀態：{oi_status}")
    print("==========================")
    market_regime = get_market_regime()

    print(f"🌎 Market Regime: {market_regime}")
    ai_score = calculate_real_ai_score(
        is_above,
        is_volume_spike,
        funding_status,
        oi_status,
        atr_status
    )
    if market_regime == "BULL":
        ai_score += 10

    return ai_score
def calculate_short_ai_score(symbol="BTC-USDT"):

    klines = get_klines(symbol)

    df = klines_to_dataframe(klines)

    latest_close = df.iloc[-1]["Close"]
    latest_ma20 = df.iloc[-1]["MA20"]

    is_below_ma20 = latest_close < latest_ma20

    is_volume_spike = check_volume_spike(df)

    atr_status = check_atr_condition(df)

    funding = get_funding_rate(symbol)
    funding_percent = parse_funding_rate(funding)
    funding_status = check_funding_condition(funding_percent)

    oi = get_open_interest(symbol)
    open_interest = parse_open_interest(oi)
    oi_status = check_oi_condition(open_interest)

    short_score = 0

    if is_below_ma20:
        short_score += 40

    if is_volume_spike:
        short_score += 20

    if is_below_ma20 and funding_status == "中性":
        short_score += 20

    if is_below_ma20 and oi_status == "資料正常":
        short_score += 20

    print("===== SHORT AI Score Debug =====")
    print(f"MA20 是否跌破：{is_below_ma20}")
    print(f"是否爆量：{is_volume_spike}")
    print(f"ATR 狀態：{atr_status}")
    print(f"Funding 狀態：{funding_status}")
    print(f"OI 狀態：{oi_status}")
    print(f"Funding 原始數值：{funding_percent}")
    print(f"OI 原始數值：{open_interest}")
    print("===============================")
    market_regime = get_market_regime()

    if market_regime == "BEAR":
        short_score += 10

    print(f"🌎 Market Regime: {market_regime}")
    return short_score