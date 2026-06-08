import time

from scanner.scanner import run_scanner
from telegram_utils.telegram_bot import send_telegram_message
from scanner.position_manager import print_open_positions

error_count = 0

send_telegram_message(
    "🚀 AI Trading System Scanner Loop 已啟動"
)

while True:

    print("\n====================")
    print("🚀 Scanner Loop Start")
    print("====================\n")

    try:

        run_scanner()

        print_open_positions()

        error_count = 0

    except Exception as e:

        error_count += 1

        print(f"❌ Scanner Error: {e}")

        send_telegram_message(
            f"""
❌ Scanner 發生錯誤

錯誤次數：{error_count}

錯誤內容：
{e}
"""
        )

        if error_count >= 5:

            send_telegram_message(
                "🛑 Scanner 連續錯誤5次，系統停止"
            )

            break

    print("⏰ 等待60秒後再次掃描...\n")

    time.sleep(60)