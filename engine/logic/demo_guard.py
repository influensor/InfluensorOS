import os
import time
from engine.config import STATE_DEMO_DIR
from engine.utils.file_utils import safe_json_load, atomic_json_write


def _state_path(customer_id, device_id):
    folder = os.path.join(STATE_DEMO_DIR, device_id)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f"{customer_id}.json")


def load_demo_state(customer_id, device_id):
    return safe_json_load(_state_path(customer_id, device_id), {
        "started_at": time.time(),
        "posts_delivered": 0
    })


def save_demo_state(customer_id, device_id, state):
    atomic_json_write(_state_path(customer_id, device_id), state)


# -------------------------
# KEEP ORIGINAL BUSINESS LOGIC
# -------------------------

def demo_allowed(customer, device_id):
    control = customer.get("demo_control")

    if not control:
        return True

    mode = control.get("mode", "posts")
    state = load_demo_state(customer["customer_id"], device_id)

    if mode == "posts":
        max_posts = control.get("max_posts")
        if max_posts is None:
            return True
        return state["posts_delivered"] < max_posts

    if mode == "time":
        max_hours = control.get("max_hours")
        if max_hours is None:
            return True

        elapsed = (time.time() - state["started_at"]) / 3600
        return elapsed < max_hours

    return True


def mark_demo_post_done(customer, device_id):
    state = load_demo_state(customer["customer_id"], device_id)
    state["posts_delivered"] += 1
    save_demo_state(customer["customer_id"], device_id, state)
