"""
Risk Score Engine V1

Purpose:
- Calculate a normalized trading risk score from 0 to 100.
- Convert the score into LOW / MEDIUM / HIGH / EXTREME risk levels.
- Provide a future input for Position Size Engine.
- Do NOT place orders.
- Do NOT modify leverage.
- Do NOT modify global risk limits.

Risk Score meaning:
0   = lowest risk
100 = highest risk
"""


MIN_RISK_SCORE = 0
MAX_RISK_SCORE = 100


def clamp_score(score):
    """
    Keep risk score between 0 and 100.
    """
    return max(MIN_RISK_SCORE, min(MAX_RISK_SCORE, float(score)))


def classify_risk_level(risk_score):
    """
    Convert numeric risk score into a risk level.
    """
    risk_score = clamp_score(risk_score)

    if risk_score < 30:
        return "LOW"

    if risk_score < 60:
        return "MEDIUM"

    if risk_score < 80:
        return "HIGH"

    return "EXTREME"


def calculate_risk_score(
    market_regime="UNKNOWN",
    atr_ratio=0.0,
    volume_ratio=1.0,
    funding_rate=0.0,
    ai_score=0.0,
):
    """
    Calculate trading risk score.

    Higher score = higher risk.

    Inputs:
    - market_regime: BULL / BEAR / RANGE / UNKNOWN
    - atr_ratio: normalized volatility ratio
    - volume_ratio: current volume / average volume
    - funding_rate: funding rate in percent
    - ai_score: trading AI score from 0 to 100
    """

    risk_score = 0.0
    reasons = []

    # --------------------------------------------------
    # 1. Market Regime Risk
    # --------------------------------------------------

    regime = str(market_regime).upper()

    regime_risk = {
        "BULL": 10,
        "BEAR": 15,
        "RANGE": 20,
        "UNKNOWN": 30,
    }.get(regime, 30)

    risk_score += regime_risk
    reasons.append(
        f"MARKET_REGIME={regime} +{regime_risk}"
    )

    # --------------------------------------------------
    # 2. ATR / Volatility Risk
    # --------------------------------------------------

    atr_ratio = max(0.0, float(atr_ratio))

    if atr_ratio >= 0.05:
        atr_risk = 25
    elif atr_ratio >= 0.03:
        atr_risk = 18
    elif atr_ratio >= 0.02:
        atr_risk = 12
    elif atr_ratio >= 0.01:
        atr_risk = 6
    else:
        atr_risk = 2

    risk_score += atr_risk
    reasons.append(
        f"ATR_RATIO={atr_ratio:.4f} +{atr_risk}"
    )

    # --------------------------------------------------
    # 3. Abnormal Volume Risk
    # --------------------------------------------------

    volume_ratio = max(0.0, float(volume_ratio))

    if volume_ratio >= 5.0:
        volume_risk = 20
    elif volume_ratio >= 3.0:
        volume_risk = 14
    elif volume_ratio >= 2.0:
        volume_risk = 8
    else:
        volume_risk = 3

    risk_score += volume_risk
    reasons.append(
        f"VOLUME_RATIO={volume_ratio:.4f} +{volume_risk}"
    )

    # --------------------------------------------------
    # 4. Funding Rate Risk
    # --------------------------------------------------

    funding_abs = abs(float(funding_rate))

    if funding_abs >= 1.0:
        funding_risk = 15
    elif funding_abs >= 0.5:
        funding_risk = 10
    elif funding_abs >= 0.2:
        funding_risk = 6
    else:
        funding_risk = 2

    risk_score += funding_risk
    reasons.append(
        f"FUNDING_ABS={funding_abs:.4f} +{funding_risk}"
    )

    # --------------------------------------------------
    # 5. AI Confidence Risk
    # --------------------------------------------------

    ai_score = clamp_score(ai_score)

    if ai_score >= 90:
        ai_risk = 2
    elif ai_score >= 80:
        ai_risk = 5
    elif ai_score >= 70:
        ai_risk = 10
    elif ai_score >= 60:
        ai_risk = 15
    else:
        ai_risk = 20

    risk_score += ai_risk
    reasons.append(
        f"AI_SCORE={ai_score:.2f} +{ai_risk}"
    )

    # --------------------------------------------------
    # Final Score
    # --------------------------------------------------

    risk_score = round(clamp_score(risk_score), 2)
    risk_level = classify_risk_level(risk_score)

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "reasons": reasons,
    }