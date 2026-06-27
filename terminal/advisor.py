from scanner.market_regime import get_market_regime


def show():
    print("=" * 60)
    print("AI Advisor")
    print("=" * 60)

    regime = get_market_regime()

    print(f"Market Regime : {regime}")
    print()

    print("Current Status")
    print("- Bot Running")
    print("- Waiting for Market Regime V2 validation")
    print()

    print("Next Target")
    print("- 30~50 new valid TP3/SL samples")
    print("- or 24~48 hours runtime")
    print()

    print("Recommendation")
    print("- Do NOT modify trading logic.")
    print("- Continue collecting samples.")
