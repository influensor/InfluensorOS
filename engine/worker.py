import time
import random

from engine.logger import info, warn, error

# =========================
# ENGINE LOGIC
# =========================
from engine.logic.customer_loader import load_all_customers
from engine.logic.post_loader import load_posts
from engine.logic.demo_guard import demo_allowed, mark_demo_post_done
from engine.logic.checkpoint_manager import (
    load as load_checkpoint,
    save as save_checkpoint,
    clear as clear_checkpoint,
)
from engine.logic.action_registry import build as build_actions
from engine.logic.comment_loader import load_random_comment
from engine.logic.delivery_tracker import mark_post_delivered

from engine.logic.rate_limiter import can_perform, record_action
from engine.logic.action_probability import (
    should_perform,
    DEMO_PROBABILITY,
    PAID_PROBABILITY,
)
from engine.logic.execution_window import enforce_execution_window
from engine.logic.device_caps import device_can_perform, record_device_action
from engine.logic.device_status import get_expected_accounts
from engine.logic.remote_config import get_config, kill_switch_active

# =========================
# UI
# =========================
from engine.ui.splash import show as show_splash
from engine.ui.instagram import (
    open_instagram,
    ui_open_profile_by_username,
    open_post_by_url,
)
from engine.ui.story_view_like import story_view_like
from engine.ui.actions import should_skip_actions
from engine.ui.view import view_post
from engine.ui.like import like_post as ui_like_post
from engine.ui.comment import post_comment
from engine.ui.repost import repost_post as ui_repost_post
from engine.ui.share import share_post as ui_share_post
from engine.ui.save import save_post as ui_save_post
from engine.ui.interested import mark_post_interested
from engine.ui.switch_account import switch_account
from engine.ui.add_to_story import add_to_story

# =========================
# CONFIG
# =========================
ACCOUNT_COOLDOWN = 3
CYCLE_COOLDOWN = 5

# =========================
# ACTION EXECUTORS
# =========================
def open_profile_by_username(device_id, account, customer):
    info(f"[{account}] Open profile @{customer['username']}", device_id)
    return ui_open_profile_by_username(device_id, customer["username"])


def like_post(device_id, account):
    return ui_like_post(device_id)


def comment_post(device_id, account, customer):
    comment = load_random_comment(customer["customer_id"])
    if not comment:
        return False
    return post_comment(device_id, comment)


def save_post(device_id, account):
    return ui_save_post(device_id)


def share_post(device_id, account):
    return ui_share_post(device_id)


def repost_post(device_id, account):
    return ui_repost_post(device_id)


def interested_post(device_id, account):
    return mark_post_interested(device_id)


def add_to_story_post(device_id, account):
    return add_to_story(device_id)


ACTION_EXECUTORS = {
    "like": like_post,
    "comment": comment_post,
    "save": save_post,
    "share": share_post,
    "repost": repost_post,
    "interested": interested_post,
    "add_to_story": add_to_story_post,
}

# =========================
# MAIN DEVICE WORKER
# =========================
def device_worker(device_id):
    info("Worker started", device_id)

    # -------------------------
    # Kill switch
    # -------------------------
    enabled, message = kill_switch_active()
    if enabled:
        error(f"KILL SWITCH ACTIVE: {message}", device_id)
        return

    show_splash(1)

    # -------------------------
    # Load checkpoint
    # -------------------------
    state = load_checkpoint(device_id) or {}

    account_index = state.get("account_index", 0)
    active_account = state.get("active_account")

    # -------------------------
    # Load customers
    # -------------------------
    customers = load_all_customers()
    demo_customers, paid_customers = [], []

    for c in customers:
        if c.get("type") == "demo":
            if demo_allowed(c, device_id):
                demo_customers.append(c)
        else:
            paid_customers.append(c)

    eligible = demo_customers if demo_customers else paid_customers
    if not eligible:
        warn("No eligible customers", device_id)
        return

    # -------------------------
    # Resume or select customer
    # -------------------------
    customer = None
    post = None

    if state.get("customer_id"):
        customer = next(
            (c for c in eligible if c["customer_id"] == state["customer_id"]),
            None
        )
        if customer:
            post = state.get("post")
            info(f"Resuming customer {customer['customer_id']}", device_id)
        else:
            clear_checkpoint(device_id)
            state = {}

    if not customer:
        customer = random.choice(eligible)
        posts = load_posts(customer["customer_id"], device_id)
        if not posts:
            warn(f"No posts for customer {customer['customer_id']}", device_id)
            return

        post = posts[0]  # latest post
        active_account = None
        account_index = 0

        save_checkpoint(device_id, {
            "customer_id": customer["customer_id"],
            "post": post,
            "account_index": 0,
            "active_account": None,
        })

    # -------------------------
    # Remote config
    # -------------------------
    profile = "demo" if customer.get("type") == "demo" else "paid"
    rate_limits = get_config("limits", {}).get(profile, {})
    action_probability = DEMO_PROBABILITY if customer.get("type") == "demo" else PAID_PROBABILITY
    execution_window = get_config("execution_window", {}).get(profile, {})
    device_caps = get_config("device_caps", {}).get(profile, {})

    enforce_execution_window(execution_window, device_id)

    # -------------------------
    # Account switch cap (NEW)
    # -------------------------
    max_account_switches = random.randint(10, 20)
    account_switch_count = 0
    info(f"Account switch cap for this cycle: {max_account_switches}",device_id)
    
    # =========================
    # ACCOUNT LOOP
    # =========================
    while True:
        # 🔴 HARD STOP: prevent infinite rotation
        if account_switch_count >= max_account_switches:
            info(
                f"Account switch limit reached "
                f"({account_switch_count}/{max_account_switches}), ending cycle",
                device_id
            )
            break

        if not active_account:
            next_account = switch_account(device_id)
            if not next_account:
                break

            active_account = next_account
            account_switch_count += 1

            save_checkpoint(device_id, {
                "customer_id": customer["customer_id"],
                "post": post,
                "account_index": account_index,
                "active_account": active_account,
            })

        info(f"Using account: {active_account}", device_id)

        # -------- PROFILE --------
        open_profile_by_username(device_id, active_account, customer)
        story_view_like(device_id)

        # -------- POST --------
        open_post_by_url(device_id, post, customer["username"])

        # -------- DECISION --------
        action_performed = False
        already_liked = should_skip_actions(device_id)

        if already_liked:
            info(f"[{active_account}] Already liked → viewing only", device_id)
            view_post(device_id, 1, random.randint(30, 60))
        else:
            actions = build_actions(customer)
            if customer["settings"].get("randomize_action_sequence"):
                random.shuffle(actions)

            for action in actions:
                if not device_can_perform(device_id, action, device_caps):
                    continue
                if not can_perform(device_id, active_account, action, rate_limits):
                    continue
                if not should_perform(action, action_probability):
                    continue

                success = (
                    comment_post(device_id, active_account, customer)
                    if action == "comment"
                    else ACTION_EXECUTORS[action](device_id, active_account)
                )

                if success:
                    action_performed = True
                    record_action(device_id, active_account, action)
                    record_device_action(device_id, action)

        # -------- DELIVERY --------
        if already_liked or action_performed:
            expected_accounts = get_expected_accounts(device_id)

            mark_post_delivered(
                customer["customer_id"],
                post,
                device_id,
                active_account,
                expected_accounts=expected_accounts,
                customer_type=customer.get("type", "paid"),
            )

        # -------- TRANSITION --------
        active_account = None
        account_index += 1
        time.sleep(ACCOUNT_COOLDOWN)

    # -------------------------
    # Demo accounting
    # -------------------------
    if customer.get("type") == "demo":
        mark_demo_post_done(customer, device_id)

    clear_checkpoint(device_id)
    info(f"Cycle completed for customer {customer['customer_id']}", device_id)
    time.sleep(CYCLE_COOLDOWN)
