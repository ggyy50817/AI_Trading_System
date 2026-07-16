from replay.replay_config import REPLAY_SYMBOLS, REPLAY_TIMEFRAME
from replay.replay_data import load_replay_klines
from replay.replay_strategy import check_entry
from replay.replay_position import ReplayPosition
from replay.replay_logger import save_trade

print("=" * 60)
print("Replay Engine V8")
print("=" * 60)

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
    last_result = None

    for i in range(60, len(df)):

        candle = df.iloc[i]
        history = df.iloc[: i + 1].copy()

        if not position.has_position():

            result = check_entry(
                history,
                symbol
            )

            last_result = result

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

            if exit_result is None:
                continue

            if "entry" not in exit_result:

                print(
                    "[PARTIAL]",
                    exit_result["reason"],
                    exit_result["price"]
                )

                continue

            trades += 1

            print(
                "[CLOSE]",
                exit_result["reason"],
                exit_result["entry"],
                "->",
                exit_result["exit"]
            )

            save_trade(
                symbol=symbol,
                side=last_result["side"],
                entry=exit_result["entry"],
                exit_price=exit_result["exit"],
                reason=exit_result["reason"],
            )

    print(f"Signals={signals} Trades={trades}")

    total_signals += signals
    total_trades += trades

print()
print("=" * 30)
print("Replay Finished")
print("Total Signals:", total_signals)
print("Total Trades :", total_trades)
