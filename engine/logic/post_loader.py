import os
from datetime import date

from engine.config import (
    DELIVERY_DIR,
    STATE_DEVICES_DIR,
)

from engine.utils.file_utils import (
    safe_json_load,
    atomic_json_write,
)


# ==================================================
# DEVICE-SPECIFIC PLAN STATE
# ==================================================

def _plan_state_path(
    customer_id,
    device_id
):

    folder = os.path.join(
        STATE_DEVICES_DIR,
        device_id,
    )

    os.makedirs(
        folder,
        exist_ok=True
    )

    return os.path.join(
        folder,
        f"post_plan_{customer_id}.json"
    )


def _load_plan_state(
    customer_id,
    device_id
):

    return safe_json_load(

        _plan_state_path(
            customer_id,
            device_id
        ),

        {
            "date": str(date.today()),
            "current_index": 0,
        }
    )


def _save_plan_state(
    customer_id,
    device_id,
    state
):

    atomic_json_write(

        _plan_state_path(
            customer_id,
            device_id
        ),

        state
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
# DELIVERY STATE
# ==================================================

def _load_delivery_state(
    customer_id,
    device_id
):

    delivery_path = os.path.join(
        DELIVERY_DIR,
        device_id,
        f"{customer_id}.json"
    )

    return safe_json_load(
        delivery_path,
        {"posts": {}}
    )


# ==================================================
# GET DELIVERY RECORD
# SUPPORTS:
# - OLD URL KEYS
# - NEW SHORTCODE KEYS
# ==================================================

def _get_delivery_record(
    posts_state,
    post
):

    shortcode = post.get(
        "shortcode"
    )

    url = post.get(
        "url"
    )

    return (

        posts_state.get(shortcode)

        or

        posts_state.get(url)

        or

        {}
    )


# ==================================================
# CHECK COMPLETED
# ==================================================

def _is_completed(record):

    return (

        str(
            record.get(
                "completed",
                False
            )
        ).lower() == "true"
    )


# ==================================================
# SINGLE POST LOADER
# ==================================================

def _single_post_per_day(

    customer_id,
    device_id,
    posts
):

    if not device_id:
        return [posts[0]]

    state = _load_plan_state(
        customer_id,
        device_id
    )

    delivery = _load_delivery_state(
        customer_id,
        device_id
    )

    posts_state = delivery.get(
        "posts",
        {}
    )

    # ---------------------------------------------
    # DAILY ROTATION
    # ---------------------------------------------

    if state["date"] != str(date.today()):

        state["date"] = str(date.today())

        state["current_index"] += 1

    total_posts = len(posts)

    start_idx = state.get(
        "current_index",
        0
    )

    # ---------------------------------------------
    # FIND FIRST INCOMPLETE POST
    # ---------------------------------------------

    for offset in range(total_posts):

        idx = (
            start_idx + offset
        ) % total_posts

        selected_post = posts[idx]

        record = _get_delivery_record(
            posts_state,
            selected_post
        )

        completed = _is_completed(
            record
        )

        print(
            f"[POST CHECK] "
            f"{selected_post['shortcode']} "
            f"completed={completed}"
        )

        # -----------------------------------------
        # SKIP COMPLETED
        # -----------------------------------------

        if completed:
            continue

        # -----------------------------------------
        # SAVE CURRENT INDEX
        # -----------------------------------------

        state["current_index"] = idx

        _save_plan_state(
            customer_id,
            device_id,
            state
        )

        return [selected_post]

    # ---------------------------------------------
    # ALL POSTS COMPLETED
    # ---------------------------------------------

    return []


# ==================================================
# MULTI POST LOADER
# ==================================================

def _multi_post_per_day(

    customer_id,
    device_id,
    posts
):

    if not device_id:
        return [posts[0]]

    # ---------------------------------------------
    # LOAD STATE
    # ---------------------------------------------

    state = _load_plan_state(
        customer_id,
        device_id
    )

    delivery = _load_delivery_state(
        customer_id,
        device_id
    )

    posts_state = delivery.get(
        "posts",
        {}
    )

    start_idx = state.get(
        "current_index",
        0
    )

    total_posts = len(posts)

    # ---------------------------------------------
    # FIND FIRST INCOMPLETE POST
    # ---------------------------------------------

    for offset in range(total_posts):

        idx = (
            start_idx + offset
        ) % total_posts

        post = posts[idx]

        record = _get_delivery_record(
            posts_state,
            post
        )

        completed = _is_completed(
            record
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

        # -----------------------------------------
        # SAVE NEXT ROTATION INDEX
        # -----------------------------------------

        state["current_index"] = (
            idx + 1
        ) % total_posts

        _save_plan_state(
            customer_id,
            device_id,
            state
        )

        return [post]

    # ---------------------------------------------
    # ALL POSTS COMPLETED
    # ---------------------------------------------

    return []


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

    # ==================================================
    # PLAN CONFIG
    # ==================================================

    plan = customer.get(
        "plan",
        {}
    )

    plan_type = plan.get(
        "type",
        "multi_post_per_day"
    )

    # ==================================================
    # SINGLE POST PLAN
    # ==================================================

    if plan_type == "single_post_per_day":

        return _single_post_per_day(

            customer_id,
            device_id,
            posts
        )

    # ==================================================
    # MULTI POST PLAN
    # ==================================================

    return _multi_post_per_day(

        customer_id,
        device_id,
        posts
    )