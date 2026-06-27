from scanner.market_regime import get_market_regime


def show():
    print("=" * 60)
    print("Market Regime")
    print("=" * 60)

    try:
        print(get_market_regime())
    except Exception as e:
        print(f"ERROR: {e}")
