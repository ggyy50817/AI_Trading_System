from replay.replay_config import REPLAY_SYMBOLS, REPLAY_TIMEFRAME
from replay.replay_data import load_replay_klines
from replay.replay_strategy import check_entry
from replay.replay_position import ReplayPosition
from replay.replay_logger import save_trade

print("="*60)
print("Replay Engine V7")
print("="*60)

total_signals = 0
total_trades = 0

for symbol in REPLAY_SYMBOLS:

    print(f"\n===== {symbol} =====")

    df = load_replay_klines(
        symbol,
        REPLAY_TIMEFRAME
    )

    position = ReplayPosition()

    signals = 0
    trades = 0

    for i in range(60, len(df)):

        candle = df.iloc[i]
        history = df.iloc[:i+1].copy()

        if not position.has_position():

            result = check_entry(history)

            if result["enter"]:

                signals += 1

                position.open_position(
                    symbol,
                    result["side"],
                    candle["Close"],
                    i
                )

        else:

            exit_result = position.update(
                candle["High"],
                candle["Low"]
            )

            if exit_result:

                if "entry" in exit_result:

                    trades += 1

                    print(
                        "[CLOSE]",
                        exit_result["reason"],
                        exit_result["entry"],
                        "->",
                        exit_result["exit"]
                    )

                    save_trade(
                        symbol,
                        position.position["side"] if position.position else result["side"],
                        exit_result["entry"],
                        exit_result["exit"],
                        exit_result["reason"]
                    )

                else:

                    print(
                        "[PARTIAL]",
                        exit_result["reason"],
                        exit_result["price"]
                    )

    print(f"Signals={signals} Trades={trades}")

    total_signals += signals
    total_trades += trades

print("\n==============================")
print("Replay Finished")
print("Total Signals:", total_signals)
print("Total Trades :", total_trades)
