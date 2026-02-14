import os
import time
from datetime import date
from engine.config import STATE_DIR
from engine.utils.file_utils import safe_json_load, atomic_json_write
os.makedirs(STATE_DIR, exist_ok=True)


DEFAULT_LIMITS = {
    "like":    {"daily": 120, "cooldown": 20},
    "comment": {"daily": 15,  "cooldown": 180},
    "save":    {"daily": 80,  "cooldown": 30},
    "share":   {"daily": 40,  "cooldown": 60},
    "repost":  {"daily": 10,  "cooldown": 300},
}


def _state_path(device_id, account):
    return os.path.join(
        STATE_DIR, f"usage_{device_id}_{account}.json"
    )


def _default_state():
    return {
        "date": str(date.today()),
        "counts": {},
        "last": {}
    }


def _load_state(device_id, account):
    path = _state_path(device_id, account)
    state = safe_json_load(path, _default_state())

    if state.get("date") != str(date.today()):
        return _default_state()

    return state


def _save_state(device_id, account, state):
    atomic_json_write(_state_path(device_id, account), state)


def can_perform(device_id, account, action, limits):
    rule = limits.get(action)
    if not rule:
        return True

    state = _load_state(device_id, account)

    count = state["counts"].get(action, 0)
    last_ts = state["last"].get(action, 0)

    if count >= rule["daily"]:
        return False

    if time.time() - last_ts < rule["cooldown"]:
        return False

    return True


def record_action(device_id, account, action):
    state = _load_state(device_id, account)

    state["counts"][action] = state["counts"].get(action, 0) + 1
    state["last"][action] = time.time()

    _save_state(device_id, account, state)
