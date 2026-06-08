import csv
import os


TRADE_LOG_FILE = "trading_log.csv"


def calculate_trade_stats():

    if not os.path.isfile(TRADE_LOG_FILE):
        return {
            "total_trades": 0,
            "win_trades": 0,
            "loss_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "average_win": 0,
            "average_loss": 0,
            "max_win_streak": 0,
            "max_loss_streak": 0
        }

    total_trades = 0
    win_trades = 0
    loss_trades = 0
    total_pnl = 0

    total_win_pnl = 0
    total_loss_pnl = 0

    current_win_streak = 0
    current_loss_streak = 0

    max_win_streak = 0
    max_loss_streak = 0

    with open(TRADE_LOG_FILE, "r", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        for row in reader:

            try:
                pnl = float(row.get("pnl", 0))
            except:
                pnl = 0

            total_pnl += pnl

            if pnl > 0:

                win_trades += 1
                total_win_pnl += pnl

                current_win_streak += 1
                current_loss_streak = 0

                if current_win_streak > max_win_streak:
                    max_win_streak = current_win_streak

            elif pnl < 0:

                loss_trades += 1
                total_loss_pnl += pnl

                current_loss_streak += 1
                current_win_streak = 0

                if current_loss_streak > max_loss_streak:
                    max_loss_streak = current_loss_streak

            else:

                current_win_streak = 0
                current_loss_streak = 0

            total_trades += 1

    if total_trades == 0:
        win_rate = 0
    else:
        win_rate = win_trades / total_trades * 100

    if win_trades == 0:
        average_win = 0
    else:
        average_win = total_win_pnl / win_trades

    if loss_trades == 0:
        average_loss = 0
    else:
        average_loss = total_loss_pnl / loss_trades

    return {
        "total_trades": total_trades,
        "win_trades": win_trades,
        "loss_trades": loss_trades,
        "win_rate": round(win_rate, 2),
        "total_pnl": round(total_pnl, 4),
        "average_win": round(average_win, 4),
        "average_loss": round(average_loss, 4),
        "max_win_streak": max_win_streak,
        "max_loss_streak": max_loss_streak
    }


if __name__ == "__main__":

    stats = calculate_trade_stats()

    print("📊 Trading Statistics v2")
    print(stats)