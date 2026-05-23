import os

from engine.config import (
    DELIVERY_DIR
)

from engine.utils.file_utils import (
    safe_json_load
)


# ==================================================
# POSTS FILE
# ==================================================

def _posts_file_path(customer_id):

    return os.path.join(

        "data",
        "posts",
        f"{customer_id}.json"
    )


# ==================================================
# LOAD POSTS
# ==================================================

def _load_posts(customer_id):

    path = _posts_file_path(
        customer_id
    )

    if not os.path.exists(path):
        return []

    data = safe_json_load(
        path,
        []
    )

    if not isinstance(data, list):
        return []

    valid_posts = []

    for post in data:

        if not isinstance(post, dict):
            continue

        if not post.get("url"):
            continue

        if not post.get("shortcode"):
            continue

        valid_posts.append(post)

    return valid_posts


# ==================================================
# DELIVERY FILE
# ==================================================

def _delivery_file_path(
    customer_id,
    device_id
):

    return os.path.join(

        DELIVERY_DIR,

        device_id,

        f"{customer_id}.json"
    )


# ==================================================
# LOAD DELIVERY
# ==================================================

def _load_delivery(
    customer_id,
    device_id
):

    path = _delivery_file_path(

        customer_id,
        device_id
    )

    return safe_json_load(

        path,

        {
            "posts": {}
        }
    )


# ==================================================
# IS COMPLETED
# ==================================================

def _is_completed(
    delivery_posts,
    post
):

    post_url = post.get(
        "url"
    )

    record = delivery_posts.get(
        post_url,
        {}
    )

    # -----------------------------------------
    # NO RECORD
    # -----------------------------------------

    if not isinstance(record, dict):
        return False

    completed = record.get(
        "completed",
        False
    )

    return bool(completed)


# ==================================================
# MAIN POST LOADER
# ==================================================

def load_posts(
    customer,
    device_id=None
):

    customer_id = customer[
        "customer_id"
    ]

    posts = _load_posts(
        customer_id
    )

    if not posts:
        return []

    # =============================================
    # NO DEVICE
    # =============================================

    if not device_id:

        return [posts[0]]

    # =============================================
    # LOAD DELIVERY
    # =============================================

    delivery = _load_delivery(

        customer_id,
        device_id
    )

    delivery_posts = delivery.get(
        "posts",
        {}
    )

    # =============================================
    # FIND FIRST INCOMPLETE
    # POSTS ARE:
    # NEWEST -> OLDEST
    # =============================================

    for post in posts:

        completed = _is_completed(
            delivery_posts,
            post
        )

        print(

            f"[POST CHECK] "
            f"{post['shortcode']} "
            f"completed={completed}"
        )

        # -----------------------------------------
        # SKIP COMPLETED
        # -----------------------------------------

        if completed:
            continue

        print(

            f"[POST SELECTED] "
            f"{post['shortcode']}"
        )

        return [post]

    # =============================================
    # ALL POSTS COMPLETED
    # =============================================

    print(
        "[POST LOADER] "
        "All posts completed"
    )

    return []