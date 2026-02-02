import os
import json
import time

from engine.config import DELIVERY_DIR
from engine.logic.device_auth import get_authorized_devices


def _path(customer_id):
    return os.path.join(DELIVERY_DIR, f"{customer_id}.json")


def _load(customer_id):
    path = _path(customer_id)

    if not os.path.exists(path):
        return {"posts": {}}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(customer_id, data):
    path = _path(customer_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# --------------------------------------------------
# PUBLIC API
# --------------------------------------------------

def device_already_done(customer_id, post_url, device_id):
    data = _load(customer_id)
    post = data["posts"].get(post_url)

    if not post:
        return False

    return device_id in post.get("devices_done", [])


def mark_device_done(customer_id, post_url, device_id):
    data = _load(customer_id)

    post = data["posts"].setdefault(post_url, {
        "devices_done": [],
        "completed": False,
        "last_update": None
    })

    if device_id not in post["devices_done"]:
        post["devices_done"].append(device_id)

    authorized = get_authorized_devices()

    if set(post["devices_done"]) >= set(authorized):
        post["completed"] = True

    post["last_update"] = int(time.time())
    _save(customer_id, data)


def get_eligible_posts(customer_id, posts, device_id):
    data = _load(customer_id)

    eligible = []

    for post in posts:
        record = data["posts"].get(post)

        if not record:
            eligible.append(post)
            continue

        if record.get("completed"):
            continue

        if device_id in record.get("devices_done", []):
            continue

        eligible.append(post)

    return eligible
