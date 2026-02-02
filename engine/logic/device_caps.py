import os
import json
import time
from datetime import date
from engine.config import STATE_DIR
os.makedirs(STATE_DIR, exist_ok=True)

# -------------------------
# DEVICE HARD CAPS (DAILY)
# -------------------------

DEVICE_DEMO_CAPS = {
    "like": 500,
    "comment": 250,
    "save": 250,
    "share": 250,
    "repost": 250,
}

DEVICE_PAID_CAPS = {
    "like": 500,
    "comment": 250,
    "save": 250,
    "share": 250,
    "repost": 250,
}


# -------------------------
# STATE HELPERS
# -------------------------
def _state_path(device_id):
    return os.path.join(STATE_DIR, f"device_{device_id}.json")


def _load_state(device_id):
    path = _state_path(device_id)

    if not os.path.exists(path):
        return {
            "date": str(date.today()),
            "counts": {},
        }

    with open(path, "r", encoding="utf-8") as f:
        state = json.load(f)

    if state.get("date") != str(date.today()):
        return {
            "date": str(date.today()),
            "counts": {},
        }

    return state


def _save_state(device_id, state):
    with open(_state_path(device_id), "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# -------------------------
# PUBLIC API
# -------------------------
def device_can_perform(device_id, action, caps):
    cap = caps.get(action)
    if cap is None:
        return True

    state = _load_state(device_id)
    count = state["counts"].get(action, 0)

    return count < cap


def record_device_action(device_id, action):
    state = _load_state(device_id)

    state["counts"][action] = state["counts"].get(action, 0) + 1
    _save_state(device_id, state)
