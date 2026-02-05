import os
import json
import time
from engine.config import STATE_DIR


def _state_path(customer_id, device_id):
    return os.path.join(
        STATE_DIR,
        f"demo_{customer_id}_{device_id}.json"
    )


def load_demo_state(customer_id, device_id):
    path = _state_path(customer_id, device_id)

    if not os.path.exists(path):
        return {
            "started_at": time.time(),
            "posts_delivered": 0
        }

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_demo_state(customer_id, device_id, state):
    path = _state_path(customer_id, device_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def demo_allowed(customer, device_id):
    control = customer.get("demo_control")

    # ✅ No demo_control → allow demo
    if not control:
        return True

    mode = control.get("mode", "posts")
    state = load_demo_state(customer["customer_id"], device_id)

    if mode == "posts":
        max_posts = control.get("max_posts")

        # ✅ No max_posts defined → unlimited demo
        if max_posts is None:
            return True

        return state["posts_delivered"] < max_posts

    if mode == "time":
        max_hours = control.get("max_hours")

        # ✅ No max_hours defined → unlimited demo
        if max_hours is None:
            return True

        elapsed = (time.time() - state["started_at"]) / 3600
        return elapsed < max_hours

    # ✅ Unknown mode → allow (fail open)
    return True


def mark_demo_post_done(customer, device_id):
    state = load_demo_state(customer["customer_id"], device_id)
    state["posts_delivered"] += 1
    save_demo_state(customer["customer_id"], device_id, state)
