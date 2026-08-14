"""
Persistent Shadow Opportunity Dedup V2

Prevent repeated scanner cycles and process restarts from creating
duplicate ShadowTrade samples for the same continuous opportunity.

A continuous opportunity is identified by:

    symbol + side + AI score + threshold + market regime

State is kept both:
- In memory for fast checks.
- On disk so collector restarts do not forget previous opportunities.

Research / observation only.
No exchange orders.
No API calls.
"""

from __future__ import annotations

import json
from pathlib import Path


DEDUP_STATE_PATH = Path("runtime/shadow/dedup_state.json")

_active_opportunities: dict[str, tuple] = {}


def build_opportunity_signature(
    symbol,
    side,
    ai_score,
    threshold,
    market_regime,
):
    """
    Build the identity of one Shadow opportunity.
    """

    return (
        str(side),
        float(ai_score),
        float(threshold),
        str(market_regime),
    )


def load_dedup_state():
    """
    Load persistent dedup state from disk.

    Missing or invalid state starts with an empty state.
    """

    _active_opportunities.clear()

    if not DEDUP_STATE_PATH.exists():
        return

    try:
        with DEDUP_STATE_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return

        for symbol, signature in data.items():
            if (
                isinstance(signature, list)
                and len(signature) == 4
            ):
                _active_opportunities[str(symbol)] = (
                    str(signature[0]),
                    float(signature[1]),
                    float(signature[2]),
                    str(signature[3]),
                )

    except (
        OSError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ):
        _active_opportunities.clear()


def save_dedup_state():
    """
    Persist the current dedup state to disk.
    """

    DEDUP_STATE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        symbol: list(signature)
        for symbol, signature
        in _active_opportunities.items()
    }

    temporary_path = DEDUP_STATE_PATH.with_suffix(
        ".tmp"
    )

    with temporary_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )

    temporary_path.replace(
        DEDUP_STATE_PATH
    )


def is_new_shadow_opportunity(
    symbol,
    side,
    ai_score,
    threshold,
    market_regime,
):
    """
    Return True only when the opportunity differs from the last
    accepted opportunity for this symbol.
    """

    symbol = str(symbol)

    signature = build_opportunity_signature(
        symbol=symbol,
        side=side,
        ai_score=ai_score,
        threshold=threshold,
        market_regime=market_regime,
    )

    previous_signature = _active_opportunities.get(
        symbol
    )

    if previous_signature == signature:
        return False

    _active_opportunities[symbol] = signature

    save_dedup_state()

    return True


def clear_shadow_opportunity(symbol):
    """
    Forget the active opportunity for one symbol.
    """

    _active_opportunities.pop(
        str(symbol),
        None,
    )

    save_dedup_state()


def clear_all_shadow_opportunities():
    """
    Reset all Shadow opportunity state.
    """

    _active_opportunities.clear()

    save_dedup_state()


load_dedup_state()
