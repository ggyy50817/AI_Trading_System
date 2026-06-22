MAX_LEVERAGE = 10
DEFAULT_MARGIN_USDT = 10

# Position Size Engine V1
# 目的：
# 1. 先用固定保證金模式取代散落式數量設定
# 2. 每單預設使用約 10 USDT 保證金
# 3. 10x 槓桿 = 約 100 USDT 名義倉位
# 4. 不提高槓桿、不提高風險，只先統一倉位計算邏輯

def calculate_position_quantity(symbol, price, margin_usdt=DEFAULT_MARGIN_USDT, leverage=MAX_LEVERAGE):
    if leverage > MAX_LEVERAGE:
        raise ValueError("leverage cannot exceed MAX_LEVERAGE")

    if price <= 0:
        raise ValueError("price must be greater than 0")

    notional_value = margin_usdt * leverage
    quantity = notional_value / price

    return quantity


def estimate_notional_value(margin_usdt=DEFAULT_MARGIN_USDT, leverage=MAX_LEVERAGE):
    if leverage > MAX_LEVERAGE:
        raise ValueError("leverage cannot exceed MAX_LEVERAGE")

    return margin_usdt * leverage
