import requests
import pandas as pd

import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from telegram_utils.telegram_bot import send_telegram_message

from ta.volatility import AverageTrueRange

BASE_URL = "https://open-api.bingx.com"


def get_symbols():

    url = f"{BASE_URL}/openApi/swap/v2/quote/contracts"

    response = requests.get(url)

    data = response.json()

    symbols = []

    for item in data["data"]:

        symbol = item["symbol"]

        if "USDT" in symbol:

            symbols.append(symbol)

    return symbols


def get_klines(symbol="BTC-USDT", interval="15m", limit=100):

    url = f"{BASE_URL}/openApi/swap/v3/quote/klines"

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    response = requests.get(url, params=params)

    data = response.json()

    return data 

def get_funding_rate(symbol="BTC-USDT"):

    url = f"{BASE_URL}/openApi/swap/v2/quote/premiumIndex"

    params = {
        "symbol": symbol
    }

    response = requests.get(url, params=params)

    data = response.json()

    return data

def get_open_interest(symbol="BTC-USDT"):

    url = f"{BASE_URL}/openApi/swap/v2/quote/openInterest"

    params = {
        "symbol": symbol
    }

    response = requests.get(url, params=params)

    data = response.json()

    return data

def parse_funding_rate(funding_data):

    funding_rate = float(funding_data["data"]["lastFundingRate"])

    funding_percent = funding_rate * 100

    return funding_percent

def parse_open_interest(oi_data):

    open_interest = float(oi_data["data"]["openInterest"])

    return open_interest

def check_oi_condition(open_interest):

    if open_interest > 0:
        return "資料正常"

    return "資料異常"

def calculate_ai_score(
    is_above,
    is_volume_spike,
    funding_status,
    oi_status,
    atr_status
):

    score = 0

    if is_above:
        score += 20

    if is_volume_spike:
        score += 20

    if funding_status == "偏多訊號":
        score += 20

    if oi_status == "資料正常":
        score += 20

    if atr_status == "波動正常":
        score += 20

    return score

def check_watchlist(ai_score):

    if ai_score >= 90:
        return "高優先級"

    if ai_score >= 85:
        return "允許開倉"

    if ai_score >= 70:
        return "加入觀察名單"

    return "忽略"

def check_funding_condition(funding_percent):

    if funding_percent <= -0.5:
        return "偏多訊號"

    if funding_percent >= 0.5:
        return "偏空訊號"

    return "中性"


def klines_to_dataframe(klines):

    data = klines.get("data", [])

    df = pd.DataFrame(data)

    if df.empty:
        raise ValueError("K線資料為空")

    df = df.rename(columns={
        "open": "Open",
        "close": "Close",
        "high": "High",
        "low": "Low",
        "volume": "Volume",
        "time": "Time"
    })

    required_columns = [
        "Open",
        "Close",
        "High",
        "Low",
        "Volume"
    ]

    missing_columns = []

    for column in required_columns:
        if column not in df.columns:
            missing_columns.append(column)

    if missing_columns:
        print("❌ K線欄位缺失：")
        print(missing_columns)
        print("原始欄位：")
        print(df.columns.tolist())
        print("原始資料前3筆：")
        print(df.head(3))
        raise ValueError(f"K線缺少必要欄位：{missing_columns}")

    df["Open"] = df["Open"].astype(float)
    df["Close"] = df["Close"].astype(float)
    df["High"] = df["High"].astype(float)
    df["Low"] = df["Low"].astype(float)
    df["Volume"] = df["Volume"].astype(float)

    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA60"] = df["Close"].rolling(window=60).mean()
    
    atr = AverageTrueRange(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=14
    )

    df["ATR"] = atr.average_true_range()

    df["VolumeMA20"] = df["Volume"].rolling(window=20).mean()

    df["VolumeRatio"] = (
        df["Volume"] / df["VolumeMA20"]
    )

    return df
def check_above_ma20(df):

    latest_close = df.iloc[-1]["Close"]

    latest_ma20 = df.iloc[-1]["MA20"]

    #print("===== MA20 Debug =====")
    #print("最新 Close:", latest_close)
    #print("最新 MA20:", latest_ma20)
    #print("最後5根 Close:")
    #print(df["Close"].tail(5))
    #print("======================")

    if latest_close > latest_ma20:
        return True

    return False

def check_volume_spike(df):

    latest_ratio = df.iloc[-1]["VolumeRatio"]

    if latest_ratio >= 2:
        return True

    return False   

def check_atr_condition(df):

    latest_atr = df.iloc[-1]["ATR"]

    if latest_atr > 0:
        return "波動正常"

    return "波動異常" 


if __name__ == "__main__":

    result = get_symbols()

    print(f"✅ 共載入 {len(result)} 個 USDT 永續合約")

    for symbol in result[:20]:
        print(symbol)

    print("\n====================\n")

    klines = get_klines("BTC-USDT")

    df = klines_to_dataframe(klines)

    print("✅ DataFrame 建立成功")

    print(
    df[
        [
            "Close",
            "MA20",
            "ATR",
            "Volume",
            "VolumeMA20",
            "VolumeRatio"
        ]
    ].tail()
)

    is_above = check_above_ma20(df)

    is_volume_spike = check_volume_spike(df)

    atr_status = check_atr_condition(df)

    print("\n====================\n")

    if is_volume_spike:
        print("🔥 發現爆量")
    else:
        print("❌ 沒有爆量")

        print(f"📊 ATR 波動狀態：{atr_status}")

    print("\n====================\n")

    if is_above:
        print("✅ 價格站上 MA20")
    else:
        print("❌ 價格跌破 MA20")

    print("\n====================\n")

    funding = get_funding_rate("BTC-USDT")

    print("✅ Funding 資金費率資料讀取成功")

    funding_percent = parse_funding_rate(funding)

    print(f"✅ 資金費率：{funding_percent:.4f}%")

    funding_status = check_funding_condition(
        funding_percent
    )

    print(f"📊 Funding 狀態：{funding_status}")

    print("\n====================\n")

    oi = get_open_interest("BTC-USDT")  

    print("✅ OI 未平倉量資料讀取成功")

    open_interest = parse_open_interest(oi)

    print(f"✅ OI 未平倉量：{open_interest}")

    oi_status = check_oi_condition(open_interest)

    print(f"📊 OI 狀態：{oi_status}")

    ai_score = calculate_ai_score(
    is_above,
    is_volume_spike,
    funding_status,
    oi_status,
    atr_status
)

    print(f"🧠 AI Score：{ai_score}")

    watchlist_status = check_watchlist(ai_score)

    print(f"📌 觀察名單狀態：{watchlist_status}")

    if watchlist_status != "忽略":

        print("\n")

        print("📌 發現高分訊號")

        print(f"🧠 AI分數：{ai_score}")

        print(f"📊 Funding：{funding_status}")

        print(f"📊 OI：{oi_status}")   
    
        message = f"""
    📌 發現高分訊號

    幣種：BTC-USDT
    AI分數：{ai_score}
    觀察狀態：{watchlist_status}

    資金費率狀態：{funding_status}
    未平倉量狀態：{oi_status}
    """

        send_telegram_message(message)