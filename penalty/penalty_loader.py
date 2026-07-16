import json
import os

FILE = "research/config/penalty.json"


def load_penalty():

    if not os.path.exists(FILE):
        return {
            "LONG": {},
            "SHORT": {}
        }

    with open(FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data.get("LONG"), dict):
        data["LONG"] = {}

    if not isinstance(data.get("SHORT"), dict):
        data["SHORT"] = {}

    return data


def save_penalty(data):

    os.makedirs(
        os.path.dirname(FILE),
        exist_ok=True
    )

    data.setdefault("LONG", {})
    data.setdefault("SHORT", {})

    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )
