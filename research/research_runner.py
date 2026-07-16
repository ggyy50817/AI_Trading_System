import json
import os

from replay.replay_core import run_replay
from replay.replay_config import (
    REPLAY_SYMBOLS,
    REPLAY_TIMEFRAME,
)


def run_research(
    symbols=None,
    timeframe=None,
    long_threshold=70,
    short_threshold=70,
    verbose=False,
):

    os.environ["LONG_THRESHOLD"] = str(long_threshold)
    os.environ["SHORT_THRESHOLD"] = str(short_threshold)

    if symbols is None:
        symbols = REPLAY_SYMBOLS

    if timeframe is None:
        timeframe = REPLAY_TIMEFRAME

    if isinstance(symbols, str):
        symbols = [symbols]

    if os.path.exists("replay_trading_log.csv"):
        os.remove("replay_trading_log.csv")

    result = run_replay(
        symbols,
        timeframe,
        verbose=verbose,
    )

    return {
        "symbols": symbols,
        "timeframe": timeframe,
        "long_threshold": long_threshold,
        "short_threshold": short_threshold,
        "signals": result["signals"],
        "trades": result["trades"],
    }


if __name__ == "__main__":

    result = run_research(
        long_threshold=70,
        short_threshold=70,
        verbose=True,
    )

    print()
    print("=" * 60)
    print("Research Runner V2")
    print("=" * 60)

    print(json.dumps(
        result,
        indent=4,
        ensure_ascii=False,
    ))
