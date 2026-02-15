import os
import time
from engine.config import DELIVERY_DIR
from engine.utils.file_utils import safe_json_load, atomic_json_write


def _path(customer_id, device_id):
    device_folder = os.path.join(DELIVERY_DIR, device_id)
    os.makedirs(device_folder, exist_ok=True)
    return os.path.join(device_folder, f"{customer_id}.json")


def _load(customer_id, device_id):
    return safe_json_load(_path(customer_id, device_id), {"posts": {}})


def _save(customer_id, device_id, data):
    atomic_json_write(_path(customer_id, device_id), data)


def device_already_done(customer_id, post_url, device_id):
    data = _load(customer_id, device_id)
    post = data["posts"].get(post_url)
    return bool(post and post.get("completed"))


def account_already_done(customer_id, post_url, device_id, account):
    if not account:
        return False

    data = _load(customer_id, device_id)
    post = data["posts"].get(post_url)
    if not post:
        return False

    return account in post.get("accounts_done", [])


def mark_post_delivered(
    customer_id,
    post_url,
    device_id,
    account,
    expected_accounts,
    customer_type="paid",
):
    if not account:
        return

    data = _load(customer_id, device_id)

    post = data["posts"].setdefault(post_url, {
        "accounts_done": [],
        "completed": False,
        "last_update": None
    })

    if account not in post["accounts_done"]:
        post["accounts_done"].append(account)

    post["completed"] = len(post["accounts_done"]) >= expected_accounts
    post["last_update"] = int(time.time())

    _save(customer_id, device_id, data)


def get_eligible_posts(customer_id, posts, device_id):
    data = _load(customer_id, device_id)
    eligible = []

    for post in posts:
        record = data["posts"].get(post)

        if not record:
            eligible.append(post)
            continue

        if record.get("completed"):
            continue

        eligible.append(post)

    return eligible
