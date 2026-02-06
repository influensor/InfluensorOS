import time
import random

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
from engine.logic.delivery_tracker import (
    mark_post_delivered,
    account_already_done,
)

from engine.logic.rate_limiter import can_perform, record_action
from engine.logic.action_probability import should_perform
from engine.logic.execution_window import enforce_execution_window
from engine.logic.device_caps import device_can_perform, record_device_action
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
from engine.ui.switch_account import switch_account

# 🟣 DEMO STORY
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
    print(f"[{device_id}] [{account}] Open profile @{customer['username']}")
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

ACTION_EXECUTORS = {
    "like": like_post,
    "comment": comment_post,
    "save": save_post,
    "share": share_post,
    "repost": repost_post,
}

# =========================
# MAIN DEVICE WORKER
# =========================
def device_worker(device_id):
    print(f"\n[{device_id}] Worker started")

    # -------------------------
    # Kill switch
    # -------------------------
    enabled, message = kill_switch_active()
    if enabled:
        print(f"[{device_id}] KILL SWITCH ACTIVE: {message}")
        return

    show_splash(1)

    # -------------------------
    # Load checkpoint (STATE IS BOSS)
    # -------------------------
    state = load_checkpoint(device_id) or {}

    account_index = state.get("account_index", 0)
    active_account = state.get("active_account")

    # -------------------------
    # Load customers (demo first)
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
        print(f"[{device_id}] No eligible customers")
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
            print(f"[{device_id}] Resuming {customer['customer_id']}")
        else:
            clear_checkpoint(device_id)
            state = {}

    if not customer:
        customer = random.choice(eligible)
        posts = load_posts(customer["customer_id"])
        if not posts:
            print(f"[{device_id}] No posts for {customer['customer_id']}")
            return

        post = random.choice(posts)

        # fresh cycle → no active account yet
        active_account = None
        account_index = 0

    # -------------------------
    # Remote config
    # -------------------------
    profile = "demo" if customer.get("type") == "demo" else "paid"
    rate_limits = get_config("limits", {}).get(profile, {})
    action_probability = get_config("probability", {}).get(profile, {})
    execution_window = get_config("execution_window", {}).get(profile, {})
    device_caps = get_config("device_caps", {}).get(profile, {})

    enforce_execution_window(execution_window, device_id)

    total_accounts = customer.get("accounts_per_device", 10)

    # =========================
    # ACCOUNT LOOP (STATE-DRIVEN)
    # =========================
    for ai in range(account_index, total_accounts):
        # -------- ACCOUNT DECISION --------
        if not active_account:
            active_account = switch_account(device_id)
            if not active_account:
                print(f"[{device_id}] Failed to switch account")
                continue

            save_checkpoint(device_id, {
                "customer_id": customer["customer_id"],
                "post": post,
                "account_index": ai,
                "active_account": active_account,
            })

        print(f"[{device_id}] Using account: {active_account}")

        # -------- PROFILE --------
        open_profile_by_username(device_id, active_account, customer)
        story_view_like(device_id)

        # -------- POST --------
        open_post_by_url(device_id, post, customer["username"])

        # -------- DECISION --------
        action_performed = False
        already_liked = should_skip_actions(device_id)

        if already_liked:
            print(f"[{device_id}] [{active_account}] Already liked → viewing")
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

                    if action == "share" and customer.get("type") == "demo":
                        add_to_story(device_id)

        # -------- DELIVERY (PER ACCOUNT) --------
        if already_liked or action_performed:
            mark_post_delivered(
                customer["customer_id"],
                post,
                device_id,
                active_account,
                expected_accounts=total_accounts,
                customer_type=customer.get("type", "paid"),
            )

        # -------- TRANSITION --------
        next_account = switch_account(device_id)

        save_checkpoint(device_id, {
            "customer_id": customer["customer_id"],
            "post": post,
            "account_index": ai + 1,
            "active_account": next_account,
        })

        active_account = next_account
        time.sleep(ACCOUNT_COOLDOWN)

    # -------------------------
    # Demo accounting
    # -------------------------
    if customer.get("type") == "demo":
        mark_demo_post_done(customer, device_id)

    clear_checkpoint(device_id)
    print(f"[{device_id}] Cycle completed for {customer['customer_id']}")
    time.sleep(CYCLE_COOLDOWN)
