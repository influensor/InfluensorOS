import os
import time
import random
from engine.config import STATE_DEVICES_DIR
from engine.utils.file_utils import safe_json_load, atomic_json_write


# ==================================================
# INTERNAL PATH
# ==================================================

def _cycle_path(device_id):
    folder = os.path.join(STATE_DEVICES_DIR, device_id)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "customer_cycle.json")


# ==================================================
# DEFAULT STATE
# ==================================================

def _default_state():
    return {
        "cycle_number": 1,
        "cycle_order": [],
        "customers_completed": [],
        "cycle_started_at": int(time.time())
    }


# ==================================================
# LOAD / SAVE
# ==================================================

def load_cycle(device_id):
    return safe_json_load(_cycle_path(device_id), _default_state())


def save_cycle(device_id, state):
    atomic_json_write(_cycle_path(device_id), state)


def reset_cycle(device_id):
    state = _default_state()
    save_cycle(device_id, state)
    return state


# ==================================================
# CORE LOGIC
# ==================================================

def _start_new_cycle(device_id, customers):
    """
    Shuffle customers once per cycle.
    """
    state = load_cycle(device_id)

    shuffled = list(customers)
    random.shuffle(shuffled)

    state["cycle_number"] += 1
    state["cycle_order"] = shuffled
    state["customers_completed"] = []
    state["cycle_started_at"] = int(time.time())

    save_cycle(device_id, state)
    return state


def get_next_customer(device_id, customers):
    """
    Returns next customer_id for this device.
    Handles:
        - first run
        - cycle completion
        - customer list changes
    """

    if not customers:
        return None

    state = load_cycle(device_id)

    # First time run or customer list changed
    if not state["cycle_order"] or set(state["cycle_order"]) != set(customers):
        state = _start_new_cycle(device_id, customers)

    completed = set(state["customers_completed"])
    ordered = state["cycle_order"]

    # Find next incomplete customer
    for cust in ordered:
        if cust not in completed:
            return cust

    # All customers completed → start new cycle
    state = _start_new_cycle(device_id, customers)
    return state["cycle_order"][0] if state["cycle_order"] else None


def mark_customer_completed(device_id, customer_id):
    state = load_cycle(device_id)

    if customer_id not in state["customers_completed"]:
        state["customers_completed"].append(customer_id)
        save_cycle(device_id, state)


def get_cycle_status(device_id):
    """
    Useful for debugging.
    """
    state = load_cycle(device_id)

    return {
        "cycle_number": state["cycle_number"],
        "total_in_cycle": len(state["cycle_order"]),
        "completed": len(state["customers_completed"]),
        "remaining": max(
            0,
            len(state["cycle_order"]) - len(state["customers_completed"])
        )
    }
