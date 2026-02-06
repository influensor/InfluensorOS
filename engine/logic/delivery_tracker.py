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
        return json.load(f)


def _save(customer_id, data):
    path = _path(customer_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ==================================================
# READ HELPERS
# ==================================================

def device_already_done(customer_id, post_url, device_id):
    data = _load(customer_id)
    post = data["posts"].get(post_url)
    if not isinstance(post, dict):
        return False

    device = post.get("devices", {}).get(device_id)
    return bool(device and device.get("completed", False))


def account_already_done(customer_id, post_url, device_id, account):
    if not account:
        return False

    data = _load(customer_id)
    post = data["posts"].get(post_url)
    if not isinstance(post, dict):
        return False

    device = post.get("devices", {}).get(device_id)
    if not isinstance(device, dict):
        return False

    return account in device.get("accounts_done", [])

# ==================================================
# WRITE DELIVERY (STRICT + SAFE)
# ==================================================

def mark_post_delivered(
    customer_id,
    post_url,
    device_id,
    account,
    expected_accounts,
    customer_type="paid",
):
    """
    Called ONLY if at least one real action succeeded.
    """
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

    # ✅ DEVICE COMPLETE ONLY WHEN ALL ACCOUNTS ACTED
    device["completed"] = len(device["accounts_done"]) >= expected_accounts

    # 🔒 GLOBAL COMPLETION ONLY FOR PAID CUSTOMERS
    if customer_type == "paid":
        authorized = get_authorized_devices()
        completed_devices = [
            d for d, info in devices.items()
            if info.get("completed")
        ]
        post["completed"] = set(completed_devices) >= set(authorized)
    else:
        # Demo never globally locks posts
        post["completed"] = False

    post["last_update"] = int(time.time())
    _save(customer_id, data)

# ==================================================
# ELIGIBILITY FILTER
# ==================================================

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
