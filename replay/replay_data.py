from scanner.bingx_api import get_klines, klines_to_dataframe

def load_replay_klines(symbol, timeframe, start=None, end=None):
    """
    Replay V2
    目前先抓最近500根K線
    後續再加入 start/end
    """
    data = get_klines(
        symbol=symbol,
        interval=timeframe,
        limit=500
    )

    df = klines_to_dataframe(data)

    return df
