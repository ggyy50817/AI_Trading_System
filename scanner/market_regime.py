from scanner.bingx_api import (
    get_klines,
    klines_to_dataframe
)


def get_market_regime():
    """
    Market Regime V1
    使用 BTC-USDT 的 MA20 / MA60 判斷大盤狀態

    BULL  = 多頭
    BEAR  = 空頭
    RANGE = 震盪
    """

    try:
        klines = get_klines("BTC-USDT")
        df = klines_to_dataframe(klines)

        latest_close = df.iloc[-1]["Close"]
        latest_ma20 = df.iloc[-1]["MA20"]
        latest_ma60 = df.iloc[-1]["MA60"]

        if latest_close > latest_ma20 and latest_ma20 > latest_ma60:
            return "BULL"

        if latest_close < latest_ma20 and latest_ma20 < latest_ma60:
            return "BEAR"

        return "RANGE"

    except Exception as e:
        print(f"Market Regime error: {e}")
        return "RANGE"
