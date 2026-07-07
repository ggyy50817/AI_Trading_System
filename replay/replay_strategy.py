from replay.replay_ai import calculate_replay_ai_context

LONG_THRESHOLD = 70
SHORT_THRESHOLD = 70


def check_entry(df):

    context = calculate_replay_ai_context(df)

    close = context["latest_close"]
    ma20 = context["latest_ma20"]

    long_score = context["long_score"]
    short_score = context["short_score"]

    if close >= ma20 and long_score >= LONG_THRESHOLD:
        return {
            "enter": True,
            "side": "LONG",
            "context": context
        }

    if close < ma20 and short_score >= SHORT_THRESHOLD:
        return {
            "enter": True,
            "side": "SHORT",
            "context": context
        }

    return {
        "enter": False,
        "side": None,
        "context": context
    }
