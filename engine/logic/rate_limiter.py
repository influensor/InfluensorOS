import os
import json
import time
from datetime import date

STATE_DIR = "runtime/state"
os.makedirs(STATE_DIR, exist_ok=True)


# -------------------------
# DEFAULT LIMITS (SAFE)
# -------------------------
DEFAULT_LIMITS = {
    "like":    {"daily": 120, "cooldown": 20},
    "comment": {"daily": 15,  "cooldown": 180},
    "save":    {"daily": 80,  "cooldown": 30},
    "share":   {"daily": 40,  "cooldown": 60},
    "repost":  {"daily": 10,  "cooldown": 300},
}

# -------------------------
# RATE LIMIT PROFILES
# -------------------------
DEMO_LIMITS = {
    "like":    {"daily": 25,  "cooldown": 60},
    "comment": {"daily": 3,   "cooldown": 600},
    "save":    {"daily": 15,  "cooldown": 90},
    "share":   {"daily": 10,  "cooldown": 120},
    "repost":  {"daily": 2,   "cooldown": 900},
}

PAID_LIMITS = {
    "like":    {"daily": 120, "cooldown": 20},
    "comment": {"daily": 15,  "cooldown": 180},
    "save":    {"daily": 80,  "cooldown": 30},
    "share":   {"daily": 40,  "cooldown": 60},
    "repost":  {"daily": 10,  "cooldown": 300},
}

# -------------------------
# STATE HELPERS
# -------------------------
def _state_path(device_id, account):
    return os.path.join(
        STATE_DIR, f"usage_{device_id}_{account}.json"
    )


def _load_state(device_id, account):
    path = _state_path(device_id, account)

    if not os.path.exists(path):
        return {
            "date": str(date.today()),
            "counts": {},
            "last": {}
        }

    with open(path, "r", encoding="utf-8") as f:
        state = json.load(f)

    # Reset if new day
    if state.get("date") != str(date.today()):
        return {
            "date": str(date.today()),
            "counts": {},
            "last": {}
        }

    return state


def _save_state(device_id, account, state):
    with open(_state_path(device_id, account), "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# -------------------------
# PUBLIC API
# -------------------------
def can_perform(device_id, account, action, limits):
    rule = limits.get(action)
    if not rule:
        return True

    state = _load_state(device_id, account)

    count = state["counts"].get(action, 0)
    last_ts = state["last"].get(action, 0)

    # Daily cap
    if count >= rule["daily"]:
        return False

    # Cooldown
    if time.time() - last_ts < rule["cooldown"]:
        return False

    return True


def record_action(device_id, account, action):
    state = _load_state(device_id, account)

    state["counts"][action] = state["counts"].get(action, 0) + 1
    state["last"][action] = time.time()

    _save_state(device_id, account, state)
