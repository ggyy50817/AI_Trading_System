from scanner.bingx_api import (
    get_klines,
    klines_to_dataframe
)
def get_market_regime():
    """
    Market Regime V1
    使用 BTC-USDT 的 MA20 / MA60 判斷大盤狀態

    BULL  = 多頭市場
    BEAR  = 空頭市場
    RANGE = 震盪市場
    """

    try:
        klines = get_klines("BTC-USDT")
        df = klines_to_dataframe(klines)

        latest_close = df.iloc[-1]["Close"]
        latest_ma20 = df.iloc[-1]["MA20"]
        latest_ma60 = df.iloc[-1]["MA60"]

        if latest_close > latest_ma20 and latest_ma20 > latest_ma60:
            regime = "BULL"

        elif latest_close < latest_ma20 and latest_ma20 < latest_ma60:
            regime = "BEAR"

        else:
            regime = "RANGE"

        print("===== Market Regime V1 =====")
        print(f"BTC Close: {latest_close}")
        print(f"BTC MA20: {latest_ma20}")
        print(f"BTC MA60: {latest_ma60}")
        print(f"Market Regime: {regime}")
        print("============================")

        return regime

    except Exception as e:
        print(f"❌ Market Regime 判斷失敗：{e}")
        return "RANGE"