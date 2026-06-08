from dotenv import load_dotenv
import os
import requests

from scanner.position_manager import print_open_positions
from scanner.scanner import run_scanner
from risk_manager.risk_manager import check_risk
from logs.logger import log_message
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, data=data)

log_message("🚀 AI Trading System Start")

send_telegram_message("🚀 AI Trading System 已啟動")

run_scanner()

check_risk()

print_open_positions()

log_message("✅ System Ready")