import json
import os

def enabled(path="control/kill_switch.json"):
    if not os.path.exists(path):
        return False

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("enabled", False)
