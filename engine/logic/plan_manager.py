import os
from datetime import date
from engine.config import PLAN_DIR

from engine.utils.file_utils import (
    safe_json_load,
    atomic_json_write,
)


# ==================================================
# PLAN STATE DIRECTORY
# ==================================================

PLAN_STATE_DIR = PLAN_DIR

# ==================================================
# STATE PATH
# ==================================================

def _state_path(
    customer_id,
    device_id
):

    device_folder = os.path.join(
        PLAN_STATE_DIR,
        device_id
    )

    os.makedirs(
        device_folder,
        exist_ok=True
    )

    return os.path.join(
        device_folder,
        f"{customer_id}.json"
    )


# ==================================================
# LOAD STATE
# ==================================================

def _load_state(
    customer_id,
    device_id
):

    today = str(date.today())

    state = safe_json_load(

        _state_path(
            customer_id,
            device_id
        ),

        {
            "date": today,
            "posts_completed_today": 0,
            "completed_today": False,
        }
    )

    # -----------------------------------------
    # RESET NEW DAY
    # -----------------------------------------

    if state.get("date") != today:

        state = {

            "date": today,

            "posts_completed_today": 0,

            "completed_today": False,
        }

        _save_state(
            customer_id,
            device_id,
            state
        )

    return state


# ==================================================
# SAVE STATE
# ==================================================

def _save_state(
    customer_id,
    device_id,
    state
):

    atomic_json_write(

        _state_path(
            customer_id,
            device_id
        ),

        state
    )


# ==================================================
# GET DAILY LIMIT
# ==================================================

def get_daily_post_limit(
    customer
):

    plan = customer.get(
        "plan",
        {}
    )

    return int(
        plan.get(
            "daily_post_limit",
            1
        )
    )


# ==================================================
# CUSTOMER COMPLETED TODAY?
# ==================================================

def customer_completed_today(
    customer,
    device_id
):

    customer_id = customer[
        "customer_id"
    ]

    state = _load_state(
        customer_id,
        device_id
    )

    return bool(
        state.get(
            "completed_today",
            False
        )
    )


# ==================================================
# MARK POST COMPLETED
# ==================================================

def mark_post_completed_today(
    customer,
    device_id
):

    customer_id = customer[
        "customer_id"
    ]

    state = _load_state(
        customer_id,
        device_id
    )

    state[
        "posts_completed_today"
    ] += 1

    limit = get_daily_post_limit(
        customer
    )

    # -----------------------------------------
    # DAILY LIMIT REACHED
    # -----------------------------------------

    if (
        state[
            "posts_completed_today"
        ] >= limit
    ):

        state[
            "completed_today"
        ] = True

    _save_state(
        customer_id,
        device_id,
        state
    )


# ==================================================
# RESET CUSTOMER
# ==================================================

def reset_customer_day(
    customer,
    device_id
):

    customer_id = customer[
        "customer_id"
    ]

    state = {

        "date": str(date.today()),

        "posts_completed_today": 0,

        "completed_today": False,
    }

    _save_state(
        customer_id,
        device_id,
        state
    )


# ==================================================
# GET STATE
# ==================================================

def get_plan_state(
    customer,
    device_id
):

    return _load_state(

        customer[
            "customer_id"
        ],

        device_id
    )