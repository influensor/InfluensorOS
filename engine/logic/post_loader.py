import os
import json
from engine.logger import info, warn
from engine.config import DELIVERY_DIR


def load_posts(customer_id, device_id=None):
    """
    Load posts for customer.
    If device_id is provided, skip posts already
    completed for that device.
    """

    # -------------------------
    # Load post list (.txt)
    # -------------------------
    path = os.path.join("data", "posts", f"{customer_id}.txt")

    if not os.path.exists(path):
        warn(f"[post_loader] post file missing: {path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        all_posts = [line.strip() for line in f if line.strip()]

    if not device_id:
        return all_posts

    # -------------------------
    # Load delivery state (.json)
    # -------------------------
    delivery_path = os.path.join(DELIVERY_DIR, f"{customer_id}.json")

    if not os.path.exists(delivery_path):
        # No delivery yet → all posts eligible
        return all_posts

    try:
        with open(delivery_path, "r", encoding="utf-8") as f:
            delivery = json.load(f)
    except Exception as e:
        warn(f"[post_loader] delivery file read error: {e}")
        return all_posts

    posts_state = delivery.get("posts", {})

    # -------------------------
    # Filter per device
    # -------------------------
    eligible_posts = []

    for post_url in all_posts:
        post_entry = posts_state.get(post_url)
        if not post_entry:
            eligible_posts.append(post_url)
            continue

        device_entry = post_entry.get("devices", {}).get(device_id)
        if device_entry and device_entry.get("completed") is True:
            continue  # 🚫 skip completed post for this device

        eligible_posts.append(post_url)

    info(
        f"[post_loader] customer={customer_id} "
        f"device={device_id} "
        f"eligible_posts={len(eligible_posts)}/{len(all_posts)}"
    )

    return eligible_posts
