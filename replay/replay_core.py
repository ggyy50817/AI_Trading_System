from replay.replay_data import load_replay_klines
from replay.replay_strategy import check_entry
from replay.replay_position import ReplayPosition
from replay.replay_logger import save_trade


def run_replay(
    symbols,
    timeframe,
    verbose=True,
):

    total_signals = 0
    total_trades = 0

    for symbol in symbols:

        if verbose:
            print(f"\n===== {symbol} =====")

        df = load_replay_klines(
            symbol,
            timeframe
        )

        position = ReplayPosition()

        signals = 0
        trades = 0
        last_result = None

        for i in range(60, len(df)):

            candle = df.iloc[i]
            history = df.iloc[:i+1].copy()

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

                    if verbose:
                        print(
                            "[PARTIAL]",
                            exit_result["reason"],
                            exit_result["price"]
                        )

                    continue

                trades += 1

                if verbose:
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
                    reason=exit_result["reason"]
                )

        if verbose:
            print(
                f"Signals={signals} Trades={trades}"
            )

        total_signals += signals
        total_trades += trades

    return {
        "signals": total_signals,
        "trades": total_trades
    }
