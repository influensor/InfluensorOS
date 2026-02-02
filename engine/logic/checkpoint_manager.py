import os
import json
from engine.config import STATE_DIR


def _path(device_id):
    return os.path.join(STATE_DIR, f"device_{device_id}.json")


def load(device_id):
    path = _path(device_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save(device_id, data):
    path = _path(device_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def clear(device_id):
    path = _path(device_id)
    if os.path.exists(path):
        os.remove(path)
