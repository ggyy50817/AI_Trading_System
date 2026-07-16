import os

from penalty.penalty_engine import apply_penalty
from research.blocklist_engine import (
    is_blocked,
    get_block_reason
)


def get_threshold(side):

    if side=="LONG":
        return int(os.environ.get("LONG_THRESHOLD","70"))

    if side=="SHORT":
        return int(os.environ.get("SHORT_THRESHOLD","70"))

    return 70


def get_research_decision(symbol,side,score):

    threshold=get_threshold(side)

    blocked=is_blocked(symbol,side)

    block_reason=None

    if blocked:
        block_reason=get_block_reason(symbol,side)

    penalty_result=apply_penalty(
        symbol,
        side,
        score
    )

    final_score=penalty_result["final_score"]

    allow=(not blocked) and final_score>=threshold

    return{

        "symbol":symbol,
        "side":side,

        "original_score":score,

        "penalty":penalty_result["penalty"],

        "final_score":final_score,

        "blocked":blocked,

        "block_reason":block_reason,

        "reverse":False,

        "threshold":threshold,

        "allow_entry":allow
    }
