from replay.replay_ai import calculate_replay_ai_context
from research.decision_engine import get_research_decision


def check_entry(df, symbol):

    context = calculate_replay_ai_context(
        df,
        symbol
    )

    close = context["latest_close"]
    ma20 = context["latest_ma20"]

    if close >= ma20:
        side = "LONG"
        score = context["long_score"]
    else:
        side = "SHORT"
        score = context["short_score"]

    decision = get_research_decision(
        symbol=symbol,
        side=side,
        score=score
    )

    return {
        "enter": decision["allow_entry"],
        "side": side,
        "context": context,
        "decision": decision
    }
