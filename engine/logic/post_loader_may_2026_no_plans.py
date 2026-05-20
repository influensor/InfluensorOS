import os
from engine.config import DELIVERY_DIR
from engine.utils.file_utils import safe_json_load


def load_posts(customer_id, device_id=None):
    path = os.path.join("data", "posts", f"{customer_id}.txt")

    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        all_posts = [line.strip() for line in f if line.strip()]

    if not device_id:
        return all_posts

    delivery_path = os.path.join(
        DELIVERY_DIR, device_id, f"{customer_id}.json"
    )

    delivery = safe_json_load(delivery_path, {"posts": {}})
    posts_state = delivery.get("posts", {})

    eligible = []

    for post_url in all_posts:
        record = posts_state.get(post_url)

        if not record:
            eligible.append(post_url)
            continue

        if record.get("completed"):
            continue

        eligible.append(post_url)

    return eligible
