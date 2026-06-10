import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from logs.trade_logger import log_close_trade

from config.settings import (
    BOT_MODE,
    MAX_POSITION,
    DEMO_TRAINING_MAX_POSITION,
    DEMO_TRADING_MAX_POSITION,
    LIVE_TRADING_MAX_POSITION
)

load_dotenv()

VST_BASE_URL = "https://open-api-vst.bingx.com"

BINGX_API_KEY = os.getenv("BINGX_API_KEY")
BINGX_SECRET_KEY = os.getenv("BINGX_SECRET_KEY")


def sign_params(params):

    query_string = urlencode(params)

    signature = hmac.new(
        BINGX_SECRET_KEY.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return query_string + "&signature=" + signature


def send_signed_request(method, path, params=None):

    if params is None:
        params = {}

    params["timestamp"] = int(time.time() * 1000)

    signed_query = sign_params(params)

    url = f"{VST_BASE_URL}{path}?{signed_query}"

    headers = {
        "X-BX-APIKEY": BINGX_API_KEY
    }

    response = requests.request(method, url, headers=headers)

    return response.json()


def get_vst_balance():

    path = "/openApi/swap/v2/user/balance"

    return send_signed_request("GET", path)

def get_vst_positions():

    path = "/openApi/swap/v2/user/positions"

    return send_signed_request("GET", path)
def get_position_by_symbol(symbol):

    positions = get_vst_positions()

    print("🔥 get_vst_positions 原始回傳：")
    print(positions)

    positions_list = positions.get("data", [])

    for position in positions_list:

        if position["symbol"] == symbol:

            return position

    return None
def calculate_tp_sl(position):

    entry_price = float(position["avgPrice"])
    position_side = position["positionSide"]

    if position_side == "LONG":
        tp1 = entry_price * 1.01
        tp2 = entry_price * 1.02
        tp3 = entry_price * 1.03
        sl = entry_price * 0.98

    elif position_side == "SHORT":
        tp1 = entry_price * 0.99
        tp2 = entry_price * 0.98
        tp3 = entry_price * 0.97
        sl = entry_price * 1.02

    else:
        return None

    return {
        "tp1": round(tp1, 6),
        "tp2": round(tp2, 6),
        "tp3": round(tp3, 6),
        "sl": round(sl, 6)
    }
def check_tp_sl_status(position, tp_sl):

    current_price = float(position["markPrice"])
    position_side = position["positionSide"]

    if position_side == "LONG":

        if current_price >= tp_sl["tp3"]:
            return "TP3_HIT"

        if current_price >= tp_sl["tp2"]:
            return "TP2_HIT"

        if current_price >= tp_sl["tp1"]:
            return "TP1_HIT"

        if current_price <= tp_sl["sl"]:
            return "STOP_LOSS_HIT"

    elif position_side == "SHORT":

        if current_price <= tp_sl["tp3"]:
            return "TP3_HIT"

        if current_price <= tp_sl["tp2"]:
            return "TP2_HIT"

        if current_price <= tp_sl["tp1"]:
            return "TP1_HIT"

        if current_price >= tp_sl["sl"]:
            return "STOP_LOSS_HIT"

    return "HOLD"
def translate_tp_sl_status(status):

    if status == "TP1_HIT":
        return "止盈1已觸發"

    if status == "TP2_HIT":
        return "止盈2已觸發"

    if status == "TP3_HIT":
        return "止盈3已觸發"

    if status == "STOP_LOSS_HIT":
        return "止損已觸發"

    return "繼續持有"
def check_breakeven(position, tp_sl_status):

    entry_price = float(position["avgPrice"])

    if tp_sl_status in [
        "TP1_HIT",
        "TP2_HIT",
        "TP3_HIT"
    ]:

        return {
            "breakeven_active": True,
            "new_stop_loss": entry_price
        }

    return {
        "breakeven_active": False,
        "new_stop_loss": None
    }
def calculate_trailing_stop(position, breakeven):

    current_price = float(position["markPrice"])
    entry_price = float(position["avgPrice"])
    position_side = position["positionSide"]

    if not breakeven["breakeven_active"]:
        return {
            "trailing_active": False,
            "trailing_stop": None
        }

    if position_side == "LONG":

        trailing_stop = current_price * 0.995

        if trailing_stop < entry_price:
            trailing_stop = entry_price

    elif position_side == "SHORT":

        trailing_stop = current_price * 1.005

        if trailing_stop > entry_price:
            trailing_stop = entry_price

    else:

        return {
            "trailing_active": False,
            "trailing_stop": None
        }

    return {
        "trailing_active": True,
        "trailing_stop": round(trailing_stop, 2)
    }
def decide_auto_close_action(tp_sl_status):

    if tp_sl_status == "TP1_HIT":
        return {
            "action": "PARTIAL_CLOSE",
            "close_percent": 30,
            "reason": "TP1 已觸發，準備平倉 30%"
        }

    if tp_sl_status == "TP2_HIT":
        return {
            "action": "PARTIAL_CLOSE",
            "close_percent": 30,
            "reason": "TP2 已觸發，準備再平倉 30%"
        }

    if tp_sl_status == "TP3_HIT":
        return {
            "action": "FULL_CLOSE",
            "close_percent": 100,
            "reason": "TP3 已觸發，準備全部平倉"
        }

    if tp_sl_status == "STOP_LOSS_HIT":
        return {
            "action": "FULL_CLOSE",
            "close_percent": 100,
            "reason": "止損已觸發，準備全部平倉"
        }

    return {
        "action": "HOLD",
        "close_percent": 0,
        "reason": "尚未觸發 TP/SL，繼續持有"
    } 
def calculate_close_quantity(position, auto_close_action):

    position_amount = float(position["positionAmt"])
    entry_price = float(position["avgPrice"])

    close_percent = auto_close_action["close_percent"]

    close_quantity = position_amount * (close_percent / 100)

    close_value = close_quantity * entry_price

    # BingX 最小平倉金額保護：
    # 如果是部分平倉，但金額太小，改成全部平倉
    if close_percent < 100 and close_value < 5:
        close_quantity = position_amount

    return round(close_quantity, 6)
def build_close_order_params(position, close_quantity):

    symbol = position["symbol"]
    position_side = position["positionSide"]

    if position_side == "LONG":
        side = "SELL"

    elif position_side == "SHORT":
        side = "BUY"

    else:
        return None

    return {
        "symbol": symbol,
        "side": side,
        "positionSide": position_side,
        "type": "MARKET",
        "quantity": close_quantity
    }
def simulate_auto_close(close_order_params):

    if not close_order_params:
        return "❌ 平倉參數錯誤"

    if close_order_params["quantity"] <= 0:
        return "📌 目前無需平倉"

    return (
        f"🚀 模擬平倉\n"
        f"幣種：{close_order_params['symbol']}\n"
        f"方向：{close_order_params['side']}\n"
        f"數量：{close_order_params['quantity']}"
    )
def parse_vst_positions(positions_data):

    positions = positions_data.get("data", [])

    parsed_positions = []

    for position in positions:

        parsed_positions.append({
            "symbol": position["symbol"],
            "side": position["positionSide"],
            "amount": position["positionAmt"],
            "avg_price": position["avgPrice"],
            "mark_price": position["markPrice"],
            "leverage": position["leverage"],
            "unrealized_profit": position["unrealizedProfit"],
            "pnl_ratio": position["pnlRatio"]
        })

    return parsed_positions

def detect_high_leverage_positions(parsed_positions, max_leverage=10):

    high_leverage_positions = []

    for position in parsed_positions:

        leverage = int(position["leverage"])

        if leverage > max_leverage:
            high_leverage_positions.append(position)

    return high_leverage_positions

def has_existing_position(symbol, position_side):

    #print("🔥 has_existing_position 被呼叫")
    #print("symbol =", symbol)

    positions_data = get_vst_positions()

    positions = positions_data.get("data", [])

    for position in positions:

        #print("===== Position Debug =====")
        #print("要檢查的幣種:", symbol)
        #print("持倉幣種:", position["symbol"])
        #print("要檢查的方向:", position_side)
        #print("持倉方向:", position["positionSide"])
        #print("持倉數量:", position["positionAmt"])

        if (
            position["symbol"] == symbol
            and position["positionSide"] == position_side
            and float(position["positionAmt"]) != 0
        ):

            #print("🚫 發現重複持倉")
            return True

    return False
def count_open_positions():

    positions_data = get_vst_positions()

    positions = positions_data.get("data", [])

    count = 0

    for position in positions:

        if float(position["positionAmt"]) != 0:
            count += 1

    return count
def get_max_position_by_mode():

    if BOT_MODE == "DEMO_TRAINING":
        return DEMO_TRAINING_MAX_POSITION

    if BOT_MODE == "DEMO_TRADING":
        return DEMO_TRADING_MAX_POSITION

    if BOT_MODE == "LIVE_TRADING":
        return LIVE_TRADING_MAX_POSITION

    return MAX_POSITION
def set_vst_leverage(symbol, position_side, leverage=10):

    path = "/openApi/swap/v2/trade/leverage"

    params = {
        "symbol": symbol,
        "side": position_side,
        "leverage": leverage
    }

    return send_signed_request(
        "POST",
        path,
        params
    )
def place_vst_market_order(
    symbol,
    side,
    position_side,
    quantity,
    leverage=10
):

    if leverage > 10:
        print("❌ 槓桿超過10x，禁止開單")
        return None

    current_position = get_position_by_symbol(symbol)

    if current_position:

        current_leverage = int(current_position["leverage"])

        if current_leverage > 10:
            print("❌ 交易所端目前槓桿超過10x，禁止開單")
            print(f"幣種：{symbol}")
            print(f"目前交易所端槓桿：{current_leverage}x")
            return None

    leverage_result = set_vst_leverage(
        symbol,
        position_side,
        leverage
    )

    print("槓桿設定結果：")
    print(leverage_result)

    if leverage_result is None or leverage_result.get("code") != 0:
        print("❌ 槓桿設定失敗，禁止開單")
        return None

    path = "/openApi/swap/v2/trade/order"

    params = {
        "symbol": symbol,
        "side": side,
        "positionSide": position_side,
        "type": "MARKET",
        "quantity": quantity
    }

    return send_signed_request(
        "POST",
        path,
        params
    )
def place_vst_close_order(close_order_params):

    if not close_order_params:
        print("❌ 平倉參數錯誤，禁止送單")
        return None

    if close_order_params["quantity"] <= 0:
        print("📌 平倉數量為 0，不送出平倉單")
        return None

    path = "/openApi/swap/v2/trade/order"

    return send_signed_request(
        "POST",
        path,
        close_order_params
    )
def safe_demo_close_test(close_order_params):

    bot_mode = os.getenv("BOT_MODE")

    if bot_mode not in ["DEMO_TRADING", "DEMO_TRAINING"]:
        print("❌ 目前不是 DEMO_TRADING / DEMO_TRAINING 模式，禁止模擬開單")
        return None

    print("⚠️ 準備送出 VST 模擬平倉單")
    print(close_order_params)

    return place_vst_close_order(close_order_params)
def calculate_close_pnl(position, close_quantity):

    entry_price = float(position["avgPrice"])
    exit_price = float(position["markPrice"])
    position_side = position["positionSide"]

    if close_quantity <= 0:
        return {
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": 0,
            "pnl_percent": 0
        }

    if position_side == "LONG":
        pnl = (exit_price - entry_price) * close_quantity

    elif position_side == "SHORT":
        pnl = (entry_price - exit_price) * close_quantity

    else:
        pnl = 0

    position_value = entry_price * close_quantity

    if position_value == 0:
        pnl_percent = 0
    else:
        pnl_percent = pnl / position_value * 100

    return {
        "entry_price": round(entry_price, 6),
        "exit_price": round(exit_price, 6),
        "pnl": round(pnl, 6),
        "pnl_percent": round(pnl_percent, 4)
    }
def execute_auto_close_and_log(
    position,
    auto_close_action,
    close_order_params
):

    close_quantity = close_order_params["quantity"]

    if close_quantity <= 0:
        print("📌 沒有觸發平倉，不寫入平倉紀錄")
        return None

    close_result = safe_demo_close_test(close_order_params)

    pnl_data = calculate_close_pnl(
        position,
        close_quantity
    )

    log_close_trade(
        symbol=position["symbol"],
        side=position["positionSide"],
        entry_price=pnl_data["entry_price"],
        exit_price=pnl_data["exit_price"],
        pnl=pnl_data["pnl"],
        pnl_percent=pnl_data["pnl_percent"],
        result=str(close_result)
    )

    return close_result
def get_demo_quantity(symbol):

    quantity_map = {
    "BTC-USDT": 0.003,
    "ETH-USDT": 0.006,
    "SOL-USDT": 0.09,
    "BNB-USDT": 0.03,
    "XRP-USDT": 6,
    "DOGE-USDT": 75,
    "SUI-USDT": 9,
    "LINK-USDT": 0.9,
    "AVAX-USDT": 3,

    "APT-USDT": 5,
    "ARB-USDT": 30,
    "OP-USDT": 25,
    "INJ-USDT": 1,
    "SEI-USDT": 50,
    "FET-USDT": 20,
    "RENDER-USDT": 3,
    "TIA-USDT": 10,
    "TON-USDT": 3,
    "NEAR-USDT": 5,
    "FIL-USDT": 5,
    "ENA-USDT": 30,
    "JUP-USDT": 30,
    "WIF-USDT": 20,
    "PEPE-USDT": 1000000
}

    return quantity_map.get(symbol, 0.001)
def safe_demo_order_test(symbol="BTC-USDT", direction="LONG"):

    bot_mode = os.getenv("BOT_MODE")

    if bot_mode not in ["DEMO_TRADING", "DEMO_TRAINING"]:
        print("❌ 目前不是 DEMO_TRADING / DEMO_TRAINING 模式，禁止模擬開單")
        return None

    if direction == "LONG":
        side = "BUY"
        position_side = "LONG"

    elif direction == "SHORT":
        side = "SELL"
        position_side = "SHORT"

    else:
        print(f"❌ 不支援的交易方向：{direction}")
        return None

    quantity = get_demo_quantity(symbol)
    leverage = 10

    if has_existing_position(symbol, position_side):
        print("❌ 已存在相同方向持倉，禁止重複開單")
        return None

    open_positions = count_open_positions()

    max_position = get_max_position_by_mode()

    if open_positions >= max_position:

        print("❌ 已達最大持倉數量，禁止開新單")
        print(f"目前持倉數：{open_positions}")
        print(f"最大允許持倉數：{max_position}")

        return None

    print("⚠️ 準備送出 VST 模擬測試單")
    print(f"幣種：{symbol}")
    print(f"方向：{position_side}")
    print(f"數量：{quantity}")
    print(f"槓桿：{leverage}x")

    return place_vst_market_order(
        symbol,
        side,
        position_side,
        quantity,
        leverage
    )

def test_position_management(symbol="BTC-USDT"):

    position = get_position_by_symbol(symbol)

    print("\n====================\n")

    print(f"{symbol} 持倉同步測試：")

    print(position)

    if not position:
        print("❌ 找不到持倉，停止測試")
        return

    tp_sl = calculate_tp_sl(position)

    print("\nTP / SL 測試：")
    print(tp_sl)

    tp_sl_status = check_tp_sl_status(
        position,
        tp_sl
    )

    print("\nTP / SL 狀態：")
    print(tp_sl_status)

    tp_sl_status_cn = translate_tp_sl_status(tp_sl_status)

    print("\nTP / SL 中文狀態：")
    print(tp_sl_status_cn)

    breakeven = check_breakeven(
        position,
        tp_sl_status
    )

    print("\n保本系統測試：")
    print(breakeven)

    trailing_stop = calculate_trailing_stop(
        position,
        breakeven
    )

    print("\n移動止損系統測試：")
    print(trailing_stop)

    auto_close_action = decide_auto_close_action(tp_sl_status)

    print("\n自動平倉決策測試：")
    print(auto_close_action)

    close_quantity = calculate_close_quantity(
        position,
        auto_close_action
    )

    print("\n自動平倉數量測試：")
    print(close_quantity)

    close_order_params = build_close_order_params(
        position,
        close_quantity
    )

    print("\n平倉單參數測試：")
    print(close_order_params)

    simulate_result = simulate_auto_close(
        close_order_params
    )

    print("\n模擬平倉測試：")
    print(simulate_result)

    close_result = execute_auto_close_and_log(
        position,
        auto_close_action,
        close_order_params
    )

    print("\nVST 模擬平倉送單測試：")

    print(close_result)
def manage_all_open_positions():

    positions_data = get_vst_positions()

    positions = positions_data.get("data", [])

    if not positions:
        print("📌 目前沒有任何持倉")
        return

    print("\n====================")
    print("📊 開始管理所有持倉")
    print("====================\n")

    for position in positions:

        if float(position["positionAmt"]) == 0:
            continue

        symbol = position["symbol"]

        print("\n====================")
        print(f"管理持倉：{symbol} {position['positionSide']}")
        print("====================")

        tp_sl = calculate_tp_sl(position)

        print("TP / SL：")
        print(tp_sl)

        tp_sl_status = check_tp_sl_status(
            position,
            tp_sl
        )

        print("TP / SL 狀態：")
        print(tp_sl_status)

        breakeven = check_breakeven(
            position,
            tp_sl_status
        )

        print("保本狀態：")
        print(breakeven)

        trailing_stop = calculate_trailing_stop(
            position,
            breakeven
        )

        print("移動止損：")
        print(trailing_stop)

        auto_close_action = decide_auto_close_action(
            tp_sl_status
        )

        print("自動平倉決策：")
        print(auto_close_action)

        close_quantity = calculate_close_quantity(
            position,
            auto_close_action
        )

        close_order_params = build_close_order_params(
            position,
            close_quantity
        )

        print("平倉單參數：")
        print(close_order_params)

        execute_auto_close_and_log(
            position,
            auto_close_action,
            close_order_params
        )    
def test_position_limit():

    open_positions = count_open_positions()

    max_position = get_max_position_by_mode()

    print("\n持倉數量限制測試：")
    print(f"目前持倉數：{open_positions}")
    print(f"最大允許持倉數：{max_position}")
def test_trailing_stop_with_fake_position():

    fake_position = {
        "symbol": "BTC-USDT",
        "positionSide": "LONG",
        "positionAmt": "0.0010",
        "avgPrice": "63390.9",
        "markPrice": "64100.0",
        "leverage": 10,
        "unrealizedProfit": "0",
        "pnlRatio": "0"
    }

    tp_sl = calculate_tp_sl(fake_position)

    print("\n假資料 TP / SL：")
    print(tp_sl)

    tp_sl_status = check_tp_sl_status(
        fake_position,
        tp_sl
    )

    print("\n假資料 TP / SL 狀態：")
    print(tp_sl_status)

    breakeven = check_breakeven(
        fake_position,
        tp_sl_status
    )

    print("\n假資料保本系統：")
    print(breakeven)

    trailing_stop = calculate_trailing_stop(
        fake_position,
        breakeven
    )

    print("\n假資料移動止損系統：")
    print(trailing_stop)
def test_short_trailing_stop_with_fake_position():

    fake_position = {
        "symbol": "BTC-USDT",
        "positionSide": "SHORT",
        "positionAmt": "0.0010",
        "avgPrice": "63390.9",
        "markPrice": "62600.0",
        "leverage": 10,
        "unrealizedProfit": "0",
        "pnlRatio": "0"
    }

    tp_sl = calculate_tp_sl(fake_position)

    print("\nSHORT 假資料 TP / SL：")
    print(tp_sl)

    tp_sl_status = check_tp_sl_status(
        fake_position,
        tp_sl
    )

    print("\nSHORT 假資料 TP / SL 狀態：")
    print(tp_sl_status)

    breakeven = check_breakeven(
        fake_position,
        tp_sl_status
    )

    print("\nSHORT 假資料保本系統：")
    print(breakeven)

    trailing_stop = calculate_trailing_stop(
        fake_position,
        breakeven
    )

    print("\nSHORT 假資料移動止損系統：")
    print(trailing_stop)
if __name__ == "__main__":

    balance = get_vst_balance()

    print("✅ VST 模擬帳戶餘額讀取結果：")
    print(balance)

    print("\n====================\n")

    positions = get_vst_positions()

    print("✅ VST 模擬持倉讀取結果：")

    parsed_positions = parse_vst_positions(positions)

    print("✅ VST 模擬持倉整理結果：")

    for position in parsed_positions:
        print(position)

    print("\n====================\n")

    high_leverage_positions = detect_high_leverage_positions(
        parsed_positions
    )

    if high_leverage_positions:

        print("⚠️ 發現超過最大槓桿限制的持倉：")

        for position in high_leverage_positions:
            print(position)

    else:
        print("✅ 所有持倉槓桿都在安全範圍內")

    test_position_management("BTC-USDT")

    test_position_limit()

    # order_result = safe_demo_order_test()
    #
    # print("✅ VST 模擬測試單結果：")
    # print(order_result)
