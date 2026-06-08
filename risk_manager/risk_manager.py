from config.settings import *

def check_risk():

    print("Risk Manager is checking risk...")

    print(f"BOT MODE: {BOT_MODE}")

    print(f"MAX LEVERAGE: {MAX_LEVERAGE}")

    print(f"MAX SINGLE RISK: {MAX_SINGLE_RISK}")

    print(f"MAX TOTAL RISK: {MAX_TOTAL_RISK}")

    print(f"MAX POSITION: {MAX_POSITION}")

    print(f"DEMO TRAINING MAX POSITION: {DEMO_TRAINING_MAX_POSITION}")

    print(f"DEMO TRADING MAX POSITION: {DEMO_TRADING_MAX_POSITION}")

    print(f"LIVE TRADING MAX POSITION: {LIVE_TRADING_MAX_POSITION}")

    print(f"FULL DEFENSE MODE: {FULL_DEFENSE_MODE}")

    print(f"BLACK SWAN MODE: {BLACK_SWAN_MODE}")

    if MANUAL_KILL_SWITCH:

        print("⚠️ MANUAL KILL SWITCH ENABLED")

        return False

    return True