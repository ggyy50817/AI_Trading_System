from logs.logger import log_message
from config.settings import BOT_MODE


DEMO_TRAINING_MIN_AI_SCORE = 80

DEMO_TRADING_MIN_AI_SCORE = 90

LIVE_TRADING_MIN_AI_SCORE = 90


def get_min_ai_score_by_mode():

    if BOT_MODE == "DEMO_TRAINING":
        return DEMO_TRAINING_MIN_AI_SCORE

    if BOT_MODE == "DEMO_TRADING":
        return DEMO_TRADING_MIN_AI_SCORE

    if BOT_MODE == "LIVE_TRADING":
        return LIVE_TRADING_MIN_AI_SCORE

    return DEMO_TRADING_MIN_AI_SCORE


def check_entry_permission(ai_score):

    min_ai_score = get_min_ai_score_by_mode()

    if ai_score >= min_ai_score:
        log_message(f"✅ AI Score {ai_score} >= {min_ai_score}，允許進入觀察名單")
        return True

    log_message(f"❌ AI Score {ai_score} < {min_ai_score}，禁止交易")
    return False