import json
import os

FILE = "research/config/blocklist.json"


def load_blocklist():

    if not os.path.exists(FILE):
        return {
            "LONG": {},
            "SHORT": {}
        }

    with open(FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data.get("LONG"), list):
        data["LONG"]={}

    if isinstance(data.get("SHORT"), list):
        data["SHORT"]={}

    data.setdefault("LONG", {})
    data.setdefault("SHORT", {})

    return data


def save_blocklist(data):

    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def is_blocked(symbol, side):

    data = load_blocklist()

    return symbol in data.get(side, {})


def get_block_reason(symbol, side):

    data = load_blocklist()

    return data.get(side, {}).get(symbol)


def add_block(
    symbol,
    side,
    samples,
    pf,
    win_rate
):

    data = load_blocklist()

    data.setdefault(side, {})

    data[side][symbol] = {
        "samples": samples,
        "pf": pf,
        "win_rate": win_rate
    }

    save_blocklist(data)


def remove_block(symbol, side):

    data = load_blocklist()

    if symbol in data.get(side, {}):

        del data[side][symbol]

        save_blocklist(data)
