import time

from scanner.scanner import run_scanner
from scanner.bingx_vst_api import manage_all_open_positions
from viewlogs.logger import log_message


SCAN_INTERVAL_SECONDS = 300


def main_loop():

    log_message("🚀 BingX AI Trading System started")

    while True:

        try:

            log_message("📊 開始管理現有持倉")
            manage_all_open_positions()

            log_message("🔍 開始掃描新訊號")
            run_scanner()

            log_message(
                f"⏳ 本輪完成，等待 {SCAN_INTERVAL_SECONDS} 秒後進入下一輪"
            )

            time.sleep(SCAN_INTERVAL_SECONDS)

        except KeyboardInterrupt:

            log_message("🛑 使用者手動停止系統")
            break

        except Exception as e:

            log_message(f"❌ 主循環錯誤：{e}")

            time.sleep(60)


if __name__ == "__main__":
    main_loop()