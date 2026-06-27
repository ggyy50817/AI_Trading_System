from scanner.bingx_vst_api import get_vst_positions


def show():
    print("=" * 60)
    print("Open Positions")
    print("=" * 60)

    try:
        data = get_vst_positions().get("data", [])

        print(f"Open Positions : {len(data)}")

        total_value = 0.0
        total_pnl = 0.0

        for p in data:
            value = float(p.get("positionValue", 0))
            pnl = float(p.get("unrealizedProfit", 0))

            total_value += value
            total_pnl += pnl

        print(f"Total Value    : {total_value:.2f}")
        print(f"UnrealizedPnL  : {total_pnl:.4f}")

    except Exception as e:
        print("ERROR:", e)
