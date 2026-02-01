import os
import json
import time

STATE_DIR = "runtime/state"

def _state_path(customer_id, device_id):
    os.makedirs(STATE_DIR, exist_ok=True)
    return os.path.join(STATE_DIR, f"demo_{customer_id}_{device_id}.json")

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
    control = customer.get("demo_control", {})
    mode = control.get("mode", "posts")

    state = load_demo_state(customer["customer_id"], device_id)

    if mode == "posts":
        max_posts = control.get("max_posts", 0)
        return state["posts_delivered"] < max_posts

    if mode == "time":
        max_hours = control.get("max_hours", 0)
        elapsed = (time.time() - state["started_at"]) / 3600
        return elapsed < max_hours

    return False

def mark_demo_post_done(customer, device_id):
    state = load_demo_state(customer["customer_id"], device_id)
    state["posts_delivered"] += 1
    save_demo_state(customer["customer_id"], device_id, state)
