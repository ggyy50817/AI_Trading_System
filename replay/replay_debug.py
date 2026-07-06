from replay.replay_config import (
    REPLAY_SYMBOL,
    REPLAY_TIMEFRAME,
)

from replay.replay_data import load_replay_klines
from replay.replay_ai import calculate_replay_ai_context

df = load_replay_klines(
    REPLAY_SYMBOL,
    REPLAY_TIMEFRAME
)

print("="*90)
print("Replay AI Debug")
print("="*90)

for i in range(60, len(df)):

    history = df.iloc[:i+1].copy()

    context = calculate_replay_ai_context(history)

    close = context["latest_close"]
    ma20 = context["latest_ma20"]
    score = context["score"]

    long_ok = close >= ma20 and score >= 70
    short_ok = close < ma20 and score >= 70

    print(
        f"{i:03d}",
        f"Close={close:.4f}",
        f"MA20={ma20:.4f}",
        f"Score={score:3}",
        f"LONG={long_ok}",
        f"SHORT={short_ok}"
    )
