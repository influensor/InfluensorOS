import os
from datetime import date
from engine.config import STATE_DIR
from engine.utils.file_utils import safe_json_load, atomic_json_write


def _state_path(device_id):
    return os.path.join(STATE_DIR, f"device_{device_id}.json")


def _default_state():
    return {
        "date": str(date.today()),
        "counts": {},
    }


def _load_state(device_id):
    path = _state_path(device_id)
    state = safe_json_load(path, _default_state())

    if state.get("date") != str(date.today()):
        return _default_state()

    return state


def _save_state(device_id, state):
    atomic_json_write(_state_path(device_id), state)


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
