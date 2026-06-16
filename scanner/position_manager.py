from scanner.bingx_vst_api import get_vst_positions, safe_demo_close_test


def get_open_vst_positions():

    positions_data = get_vst_positions()

    positions = positions_data.get("data", [])

    open_positions = []

    for position in positions:

        position_amount = float(position["positionAmt"])

        if position_amount != 0:

            open_positions.append(position)

    return open_positions

def should_stop_loss(position, max_loss_ratio=-0.08):

    pnl_ratio = float(position["pnlRatio"])

    if pnl_ratio <= max_loss_ratio:
        return True

    return False
def get_take_profit_level(position):

    pnl_ratio = float(position["pnlRatio"])

    if pnl_ratio >= 0.20:
        return {
            "level": "TP3",
            "close_percent": 100
        }

    if pnl_ratio >= 0.10:
        return {
            "level": "TP2",
            "close_percent": 0
        }

    if pnl_ratio >= 0.05:
        return {
            "level": "TP1",
            "close_percent": 0
        }

    return None
def build_stop_loss_close_params(position):

    symbol = position["symbol"]
    position_side = position["positionSide"]
    quantity = float(position["positionAmt"])

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
    "quantity": quantity
}
def build_take_profit_close_params(position, take_profit):

    symbol = position["symbol"]
    position_side = position["positionSide"]

    position_amount = float(position["positionAmt"])
    close_percent = take_profit["close_percent"]

    quantity = position_amount * (close_percent / 100)
    quantity = round(quantity, 6)

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
        "quantity": quantity
    }
def execute_stop_loss_close(position):

    close_params = build_stop_loss_close_params(position)

    if close_params is None:
        print("❌ 止損平倉參數錯誤")
        return None

    print("⚠️ 準備執行止損平倉")
    print(close_params)

    close_result = safe_demo_close_test(close_params)

    print("✅ 止損平倉結果：")
    print(close_result)

    return close_result
def execute_take_profit_close(position, take_profit):

    close_params = build_take_profit_close_params(
        position,
        take_profit
    )

    if close_params is None:
        print("❌ 止盈平倉參數錯誤")
        return None

    if close_params["quantity"] <= 0:
        print(f"📌 {take_profit['level']} 已達成，但小倉位測試模式暫不部分平倉")
        return None

    print(f"🎯 已達 {take_profit['level']} 條件")
    print("⚠️ 準備執行止盈平倉")
    print(close_params)

    close_result = safe_demo_close_test(close_params)

    print("✅ 止盈平倉結果：")
    print(close_result)

    return close_result
def print_open_positions():

    open_positions = get_open_vst_positions()

    print("\n====================")
    print("📌 目前 VST 持倉")
    print("====================")

    if not open_positions:
        print("目前沒有持倉")
        return

    for position in open_positions:

        print(f"幣種：{position['symbol']}")
        print(f"方向：{position['positionSide']}")
        print(f"數量：{position['positionAmt']}")
        print(f"開倉均價：{position['avgPrice']}")
        print(f"標記價格：{position['markPrice']}")
        print(f"槓桿：{position['leverage']}x")
        print(f"未實現盈虧：{position['unrealizedProfit']}")
        print(f"盈虧比例：{position['pnlRatio']}")
        if should_stop_loss(position):
            print("🚨 已達止損條件，但 print_open_positions 只顯示，不執行平倉")

        else:
            print("✅ 尚未達止損條件")

            take_profit = get_take_profit_level(position)

            if take_profit:
                print(f"🎯 已達 {take_profit['level']} 條件，但 print_open_positions 只顯示，不執行平倉")
            else:
                print("📌 尚未達止盈條件")
        print("--------------------")


if __name__ == "__main__":

    print_open_positions()