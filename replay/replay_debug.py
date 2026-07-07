from replay.replay_config import (
    REPLAY_SYMBOLS,
    REPLAY_TIMEFRAME,
)

from replay.replay_data import load_replay_klines
from replay.replay_ai import calculate_replay_ai_context

print("=" * 90)
print("Replay AI Debug V8")
print("=" * 90)

for symbol in REPLAY_SYMBOLS:

    print()
    print("==========", symbol, "==========")

    df = load_replay_klines(
        symbol,
        REPLAY_TIMEFRAME
    )

    for i in range(60, len(df)):

        history = df.iloc[:i+1].copy()

        context = calculate_replay_ai_context(history)

        close = context["latest_close"]
        ma20 = context["latest_ma20"]

        long_score = context["long_score"]
        short_score = context["short_score"]

        long_ok = close >= ma20 and long_score >= 70
        short_ok = close < ma20 and short_score >= 70

        if long_ok or short_ok:

            print(
                f"{i:03d}",
                f"Close={close:.4f}",
                f"MA20={ma20:.4f}",
                f"L={long_score:3}",
                f"S={short_score:3}",
                f"LONG={long_ok}",
                f"SHORT={short_ok}",
            )
