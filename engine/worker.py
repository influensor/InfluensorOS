import os
import time
import random

from engine.config import ACCOUNTS_DIR

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

# Delivery tracker (NEW)
from engine.logic.delivery_tracker import (
    get_eligible_posts,
    mark_device_done,
)

# Rate limiter (per account)
from engine.logic.rate_limiter import can_perform, record_action

# Action probability
from engine.logic.action_probability import should_perform

# Execution window
from engine.logic.execution_window import enforce_execution_window

# Device hard caps
from engine.logic.device_caps import device_can_perform, record_device_action

# Remote config
from engine.logic.remote_config import get_config, kill_switch_active

# =========================
# UI / UIAUTOMATOR2
# =========================
from engine.ui.splash import show as show_splash
from engine.ui.instagram import (
    open_instagram,
    open_profile_by_username,
    open_post_by_url,
)
from engine.ui.actions import like_post as ui_like_post
from engine.ui.comment import post_comment
from engine.ui.save import save_post as ui_save_post
from engine.ui.share import share_post as ui_share_post
from engine.ui.repost import repost_post as ui_repost_post

# =========================
# BASIC CONFIG
# =========================
ACCOUNT_COOLDOWN = 3
CYCLE_COOLDOWN = 5


# =========================
# UI ACTION WRAPPERS
# =========================
def like_post(device_id, account):
    print(f"[{device_id}] [{account}] Like (UI)")
    return ui_like_post(device_id)


def comment_post(device_id, account, customer):
    comment = load_random_comment(customer["customer_id"])
    if not comment:
        print(f"[{device_id}] [{account}] No comment available, skipping")
        return False

    print(f"[{device_id}] [{account}] Comment (UI)")
    return post_comment(device_id, comment)


def save_post(device_id, account):
    print(f"[{device_id}] [{account}] Save (UI)")
    return ui_save_post(device_id)


def share_post(device_id, account):
    print(f"[{device_id}] [{account}] Share (UI)")
    return ui_share_post(device_id)


def repost_post(device_id, account):
    print(f"[{device_id}] [{account}] Repost (UI)")
    return ui_repost_post(device_id)


ACTION_EXECUTORS = {
    "like": like_post,
    "save": save_post,
    "share": share_post,
    "repost": repost_post,
}


# =========================
# LOAD ACCOUNTS PER DEVICE
# =========================
def load_accounts(device_id):
    path = os.path.join(
        ACCOUNTS_DIR,
        f"device_{device_id}_accounts.txt"
    )

    if not os.path.exists(path):
        return ["acc_1", "acc_2", "acc_3"]

    with open(path, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]


# =========================
# MAIN DEVICE WORKER
# =========================
def device_worker(device_id):
    print(f"\n[{device_id}] Worker started")

    # -------------------------
    # Kill switch (REMOTE)
    # -------------------------
    enabled, message = kill_switch_active()
    if enabled:
        print(f"[{device_id}] KILL SWITCH ACTIVE: {message}")
        return

    # -------------------------
    # Splash screen
    # -------------------------
    show_splash(10)

    # -------------------------
    # Load checkpoint
    # -------------------------
    checkpoint = load_checkpoint(device_id)

    # -------------------------
    # Load customers
    # -------------------------
    customers = load_all_customers()
    eligible = []

    for c in customers:
        if c.get("type") == "demo":
            if demo_allowed(c, device_id):
                eligible.append(c)
        else:
            eligible.append(c)

    if not eligible:
        print(f"[{device_id}] No eligible customers")
        return

    # -------------------------
    # Select or resume customer
    # -------------------------
    if checkpoint:
        customer = next(
            c for c in eligible
            if c["customer_id"] == checkpoint["customer_id"]
        )

        post = checkpoint["post"]
        account_index = checkpoint["account_index"]
        step_index = checkpoint["step_index"]

        print(f"[{device_id}] Resuming {customer['customer_id']} | {post}")

    else:
        customer = random.choice(eligible)

        posts = load_posts(customer["customer_id"])
        posts = get_eligible_posts(
            customer["customer_id"],
            posts,
            device_id
        )

        if not posts:
            print(f"[{device_id}] No eligible posts left for {customer['customer_id']}")
            return

        post = random.choice(posts)
        account_index = 0
        step_index = 0

        save_checkpoint(device_id, {
            "customer_id": customer["customer_id"],
            "post": post,
            "account_index": 0,
            "step_index": 0,
        })

        print(f"[{device_id}] Selected {customer['customer_id']} | {post}")

    # -------------------------
    # LOAD REMOTE CONFIG
    # -------------------------
    profile = "demo" if customer.get("type") == "demo" else "paid"

    rate_limits = get_config("limits", {}).get(profile, {})
    action_probability = get_config("probability", {}).get(profile, {})
    execution_window = get_config("execution_window", {}).get(profile, {})
    device_caps = get_config("device_caps", {}).get(profile, {})

    # -------------------------
    # Enforce execution window
    # -------------------------
    enforce_execution_window(execution_window, device_id)

    # -------------------------
    # Accounts loop
    # -------------------------
    accounts = load_accounts(device_id)

    for ai in range(account_index, len(accounts)):
        account = accounts[ai]
        print(f"[{device_id}] Switching account → {account}")

        # Navigation
        open_instagram(device_id)
        open_profile_by_username(device_id, customer["username"])
        open_post_by_url(device_id, post)

        actions = build_actions(customer)

        if customer["settings"].get("randomize_action_sequence"):
            random.shuffle(actions)

        for si in range(step_index, len(actions)):
            action = actions[si]

            # -------------------------
            # Device hard cap
            # -------------------------
            if not device_can_perform(device_id, action, device_caps):
                print(f"[{device_id}] {action} skipped (device cap)")
                continue

            # -------------------------
            # Account rate limit
            # -------------------------
            if not can_perform(device_id, account, action, rate_limits):
                print(f"[{device_id}] [{account}] {action} skipped (rate limit)")
                continue

            # -------------------------
            # Probability check
            # -------------------------
            if not should_perform(action, action_probability):
                print(f"[{device_id}] [{account}] {action} skipped (probability)")
                continue

            success = False

            if action == "comment":
                success = comment_post(device_id, account, customer)
            else:
                executor = ACTION_EXECUTORS.get(action)
                if executor:
                    success = executor(device_id, account)

            if success:
                record_action(device_id, account, action)
                record_device_action(device_id, action)

            save_checkpoint(device_id, {
                "customer_id": customer["customer_id"],
                "post": post,
                "account_index": ai,
                "step_index": si + 1,
            })

        step_index = 0

        save_checkpoint(device_id, {
            "customer_id": customer["customer_id"],
            "post": post,
            "account_index": ai + 1,
            "step_index": 0,
        })

        time.sleep(ACCOUNT_COOLDOWN)

    # -------------------------
    # Mark delivery complete (PER DEVICE)
    # -------------------------
    mark_device_done(
        customer["customer_id"],
        post,
        device_id
    )

    # -------------------------
    # Demo accounting
    # -------------------------
    if customer.get("type") == "demo":
        mark_demo_post_done(customer, device_id)

    clear_checkpoint(device_id)
    print(f"[{device_id}] Cycle completed for {customer['customer_id']}")

    time.sleep(CYCLE_COOLDOWN)
