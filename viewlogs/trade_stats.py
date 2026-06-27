import csv
import os


TRADE_LOG_FILE = "trading_log.csv"


def is_success_trade(result_text):
    return "'code': 0" in result_text or '"code": 0' in result_text


def calculate_trade_stats():

    if not os.path.isfile(TRADE_LOG_FILE):
        return {}

    total_rows = 0
    success_trades = 0
    failed_trades = 0

    win_trades = 0
    loss_trades = 0
    total_pnl = 0
    total_win_pnl = 0
    total_loss_pnl = 0

    with open(TRADE_LOG_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            total_rows += 1

            result_text = row.get("result", "")

            if not is_success_trade(result_text):
                failed_trades += 1
                continue

            try:
                pnl = float(row.get("pnl", 0))
            except:
                pnl = 0

            success_trades += 1
            total_pnl += pnl

            if pnl > 0:
                win_trades += 1
                total_win_pnl += pnl
            elif pnl < 0:
                loss_trades += 1
                total_loss_pnl += pnl

    win_rate = (win_trades / success_trades * 100) if success_trades else 0
    average_win = (total_win_pnl / win_trades) if win_trades else 0
    average_loss = (total_loss_pnl / loss_trades) if loss_trades else 0

    return {
        "total_rows": total_rows,
        "success_trades": success_trades,
        "failed_trades": failed_trades,
        "win_trades": win_trades,
        "loss_trades": loss_trades,
        "win_rate": round(win_rate, 2),
        "gross_pnl": round(total_pnl, 4),
        "average_win": round(average_win, 4),
        "average_loss": round(average_loss, 4),
        "note": "目前尚未扣除手續費與 Funding Fee"
    }


if __name__ == "__main__":
    stats = calculate_trade_stats()

    print("📊 Trading Statistics V1")
    for key, value in stats.items():
        print(f"{key}: {value}")
