import os
import json
import time
from datetime import date
from engine.config import STATE_DIR
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

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                raise ValueError("Empty JSON file")
            state = json.loads(content)
    except Exception:
        # Corrupted file → reset safely
        return {
            "date": str(date.today()),
            "counts": {},
            "last": {}
        }

    # Reset if new day
    if state.get("date") != str(date.today()):
        return {
            "date": str(date.today()),
            "counts": {},
            "last": {}
        }

    return state


import tempfile

def _save_state(device_id, account, state):
    path = _state_path(device_id, account)
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        "w",
        delete=False,
        dir=directory,
        encoding="utf-8"
    ) as tmp:
        json.dump(state, tmp, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())
        temp_name = tmp.name

    os.replace(temp_name, path)


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
