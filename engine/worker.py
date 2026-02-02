import os
import time
import random

# =========================
# ENGINE LOGIC IMPORTS
# =========================
from engine.logic.customer_loader import load_all_customers
from engine.logic.demo_guard import demo_allowed, mark_demo_post_done
from engine.logic.post_loader import load_posts
from engine.logic.comment_loader import load_random_comment
from engine.logic.checkpoint_manager import (
    load as load_checkpoint,
    save as save_checkpoint,
    clear as clear_checkpoint,
)
from engine.logic.action_registry import build as build_actions

# =========================
# UI IMPORTS (UIAUTOMATOR2)
# =========================
from engine.ui.splash import show as show_splash
from engine.ui.instagram import (
    open_instagram,
    open_profile_by_username,
    open_post_by_url,
)
from engine.ui.actions import like_post as ui_like_post
from engine.ui.comment import post_comment

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
        print(f"[{device_id}] No comment available")
        return False

    print(f"[{device_id}] [{account}] Comment (UI)")
    return post_comment(device_id, comment)


def save_post(device_id, account):
    print(f"[{device_id}] [{account}] Save (UI placeholder)")
    time.sleep(1)


def share_post(device_id, account):
    print(f"[{device_id}] [{account}] Share (UI placeholder)")
    time.sleep(1)


def repost_post(device_id, account):
    print(f"[{device_id}] [{account}] Repost (UI placeholder)")
    time.sleep(1)


def share_to_story(device_id, account):
    print(f"[{device_id}] [{account}] Share to Story (UI placeholder)")
    time.sleep(1)


# =========================
# ACTION EXECUTOR MAP
# (context-free actions only)
# =========================
ACTION_EXECUTORS = {
    "like": like_post,
    "save": save_post,
    "share": share_post,
    "repost": repost_post,
    "share_to_story": share_to_story,
}


# =========================
# ACCOUNTS PER DEVICE
# =========================
def load_accounts(device_id):
    path = f"runtime/accounts/device_{device_id}_accounts.txt"
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
    # Resume checkpoint if any
    # -------------------------
    checkpoint = load_checkpoint(device_id)

    # -------------------------
    # Step 6: Splash Screen
    # -------------------------
    show_splash(30)

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
    # Select or Resume Customer
    # -------------------------
    if checkpoint:
        customer_id = checkpoint["customer_id"]
        post = checkpoint["post"]
        account_index = checkpoint["account_index"]
        step_index = checkpoint["step_index"]

        customer = next(c for c in eligible if c["customer_id"] == customer_id)
        print(f"[{device_id}] Resuming {customer_id} | {post}")

    else:
        customer = random.choice(eligible)
        posts = load_posts(customer["customer_id"])

        if not posts:
            print(f"[{device_id}] No posts for {customer['customer_id']}")
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
    # Account Loop
    # -------------------------
    accounts = load_accounts(device_id)

    for ai in range(account_index, len(accounts)):
        account = accounts[ai]
        print(f"[{device_id}] Switching account → {account}")

        # Navigation
        open_instagram(device_id)
        open_profile_by_username(device_id, customer["username"])
        open_post_by_url(device_id, post)

        # Actions
        actions = build_actions(customer)
        if customer["settings"].get("randomize_action_sequence"):
            random.shuffle(actions)

        for si in range(step_index, len(actions)):
            action = actions[si]

            if action == "comment":
                comment_post(device_id, account, customer)
            else:
                executor = ACTION_EXECUTORS.get(action)
                if executor:
                    executor(device_id, account)

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
    # Demo accounting
    # -------------------------
    if customer.get("type") == "demo":
        mark_demo_post_done(customer, device_id)

    clear_checkpoint(device_id)
    print(f"[{device_id}] Cycle completed for {customer['customer_id']}")

    time.sleep(CYCLE_COOLDOWN)
