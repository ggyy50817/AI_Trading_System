from replay.replay_config import REPLAY_SYMBOL, REPLAY_TIMEFRAME, REPLAY_START, REPLAY_END
from replay.replay_data import load_replay_klines

def main():
    print("===== Replay Engine V1 =====")
    print("Symbol:", REPLAY_SYMBOL)
    print("Timeframe:", REPLAY_TIMEFRAME)
    print("Start:", REPLAY_START)
    print("End:", REPLAY_END)

    klines = load_replay_klines(
        REPLAY_SYMBOL,
        REPLAY_TIMEFRAME,
        REPLAY_START,
        REPLAY_END
    )

    print("Loaded klines:", len(klines))
    print("Replay V1 skeleton OK")

if __name__ == "__main__":
    main()
