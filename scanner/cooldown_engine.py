import json
import os
from datetime import datetime, timedelta

COOLDOWN_FILE = "cooldown_state.json"

COOLDOWN_MINUTES = 60


def load_cooldown():

    if not os.path.exists(COOLDOWN_FILE):
        return {}

    try:
        with open(COOLDOWN_FILE, "r") as f:
            return json.load(f)

    except:
        return {}


def save_cooldown(data):

    with open(COOLDOWN_FILE, "w") as f:
        json.dump(data, f, indent=4)


def add_cooldown(symbol):

    data = load_cooldown()

    data[symbol] = datetime.now().isoformat()

    save_cooldown(data)


def is_in_cooldown(symbol):

    data = load_cooldown()

    if symbol not in data:
        return False

    stop_time = datetime.fromisoformat(
        data[symbol]
    )

    expire_time = stop_time + timedelta(
        minutes=COOLDOWN_MINUTES
    )

    return datetime.now() < expire_time
