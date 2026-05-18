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

def _plan_state_path(customer_id, device_id):
    folder = os.path.join(
        STATE_DEVICES_DIR,
        device_id,
    )

    os.makedirs(folder, exist_ok=True)

    return os.path.join(
        folder,
        f"post_plan_{customer_id}.json"
    )


def _load_plan_state(customer_id, device_id):
    return safe_json_load(
        _plan_state_path(customer_id, device_id),
        {
            "date": str(date.today()),
            "current_index": 0,
        }
    )


def _save_plan_state(customer_id, device_id, state):
    atomic_json_write(
        _plan_state_path(customer_id, device_id),
        state
    )


# ==================================================
# MAIN POST LOADER
# ==================================================

def load_posts(customer, device_id=None):

    customer_id = customer["customer_id"]

    path = os.path.join(
        "data",
        "posts",
        f"{customer_id}.txt"
    )

    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:

        all_posts = [
            line.strip()
            for line in f
            if line.strip()
        ]

    if not all_posts:
        return []

    # ==================================================
    # PLAN CONFIG
    # ==================================================

    plan = customer.get("plan", {})

    plan_type = plan.get(
        "type",
        "multi_post_per_day"
    )

    # ==================================================
    # SINGLE POST PER DAY
    # ==================================================

    if plan_type == "single_post_per_day":

        if not device_id:
            return [all_posts[0]]

        state = _load_plan_state(
            customer_id,
            device_id
        )

        # ------------------------------------------
        # DAILY ROTATION
        # ------------------------------------------

        if state["date"] != str(date.today()):

            state["date"] = str(date.today())

            state["current_index"] += 1

        idx = state["current_index"]

        if idx >= len(all_posts):

            idx = 0
            state["current_index"] = 0

        selected_post = all_posts[idx]

        # ------------------------------------------
        # DELIVERY CHECK
        # ------------------------------------------

        delivery_path = os.path.join(
            DELIVERY_DIR,
            device_id,
            f"{customer_id}.json"
        )

        delivery = safe_json_load(
            delivery_path,
            {"posts": {}}
        )

        posts_state = delivery.get("posts", {})

        record = posts_state.get(selected_post)

        # ------------------------------------------
        # TODAY'S POST ALREADY COMPLETED
        # ------------------------------------------

        if record and record.get("completed"):

            _save_plan_state(
                customer_id,
                device_id,
                state
            )

            return []

        # ------------------------------------------
        # RETURN TODAY'S ASSIGNED POST
        # ------------------------------------------

        _save_plan_state(
            customer_id,
            device_id,
            state
        )

        return [selected_post]

    # ==================================================
    # MULTI POST PER DAY
    # ==================================================

    if not device_id:
        return [all_posts[0]]

    state = _load_plan_state(
        customer_id,
        device_id
    )

    idx = state.get("current_index", 0)

    if idx >= len(all_posts):

        idx = 0
        state["current_index"] = 0

    selected_post = all_posts[idx]

    # ------------------------------------------
    # ROTATE FOR NEXT CYCLE
    # ------------------------------------------

    state["current_index"] += 1

    if state["current_index"] >= len(all_posts):
        state["current_index"] = 0

    _save_plan_state(
        customer_id,
        device_id,
        state
    )

    return [selected_post]