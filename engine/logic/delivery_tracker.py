import os
import json
import time

from engine.config import DELIVERY_DIR
from engine.logic.device_auth import get_authorized_devices


# ==================================================
# INTERNAL HELPERS
# ==================================================

def _path(customer_id):
    os.makedirs(DELIVERY_DIR, exist_ok=True)
    return os.path.join(DELIVERY_DIR, f"{customer_id}.json")


def _load(customer_id):
    path = _path(customer_id)

    if not os.path.exists(path):
        return {"posts": {}}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 🔁 AUTO-MIGRATE legacy format if found
    migrated = False

    for post_url, post in list(data.get("posts", {}).items()):
        # LEGACY FORMAT DETECTED
        if isinstance(post, dict) and "devices_done" in post:
            new_devices = {}

            for device_id in post.get("devices_done", []):
                new_devices[device_id] = {
                    "accounts_done": [],
                    "completed": True
                }

            data["posts"][post_url] = {
                "devices": new_devices,
                "completed": post.get("completed", False),
                "last_update": post.get("last_update")
            }
            migrated = True

    if migrated:
        _save(customer_id, data)

    return data


def _save(customer_id, data):
    path = _path(customer_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ==================================================
# PUBLIC API
# ==================================================

def account_already_done(customer_id, post_url, device_id, account):
    if not account:
        return False

    data = _load(customer_id)
    post = data["posts"].get(post_url)

    if not isinstance(post, dict):
        return False

    devices = post.get("devices", {})
    device = devices.get(device_id)

    if not isinstance(device, dict):
        return False

    return account in device.get("accounts_done", [])


def mark_post_delivered(customer_id, post_url, device_id, account):
    if not account:
        return

    data = _load(customer_id)

    post = data["posts"].setdefault(post_url, {
        "devices": {},
        "completed": False,
        "last_update": None
    })

    devices = post.setdefault("devices", {})

    device = devices.setdefault(device_id, {
        "accounts_done": [],
        "completed": False
    })

    if account not in device["accounts_done"]:
        device["accounts_done"].append(account)

    device["completed"] = True

    # GLOBAL COMPLETION CHECK
    authorized = get_authorized_devices()
    completed_devices = [
        d for d, info in devices.items()
        if info.get("completed")
    ]

    if set(completed_devices) >= set(authorized):
        post["completed"] = True

    post["last_update"] = int(time.time())
    _save(customer_id, data)


def get_eligible_posts(customer_id, posts, device_id):
    data = _load(customer_id)
    eligible = []

    for post in posts:
        record = data["posts"].get(post)

        if not isinstance(record, dict):
            eligible.append(post)
            continue

        if record.get("completed"):
            continue

        device = record.get("devices", {}).get(device_id)
        if device and device.get("completed"):
            continue

        eligible.append(post)

    return eligible
