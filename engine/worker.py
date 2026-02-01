import os
import time
import random

from engine.ui.instagram import (
    open_instagram,
    open_post_by_url,
    open_profile_by_username
)
from engine.ui.actions import like_post as ui_like_post

from engine.logic.customer_loader import load_all_customers
from engine.logic.demo_guard import demo_allowed, mark_demo_post_done
from engine.logic.post_loader import load_posts
from engine.logic.checkpoint_manager import (
    load as load_checkpoint,
    save as save_checkpoint,
    clear as clear_checkpoint
)
from engine.logic.action_registry import build as build_actions
from engine.ui.splash import show as show_splash


# =========================
# BASIC CONFIG
# =========================
ACCOUNT_COOLDOWN = 3
CYCLE_COOLDOWN = 5


# =========================
# PLACEHOLDER ACTIONS
# (UiAutomator2 later)
# =========================
def open_post(device_id, account, post):
    print(f"[{device_id}] [{account}] Open post {post}")
    time.sleep(1)

def like_post(device_id, account):
    print(f"[{device_id}] [{account}] Like (UI)")
    return ui_like_post(device_id)

def comment_post(device_id, account):
    print(f"[{device_id}] [{account}] Comment")
    time.sleep(1)

def save_post(device_id, account):
    print(f"[{device_id}] [{account}] Save")
    time.sleep(1)

def share_post(device_id, account):
    print(f"[{device_id}] [{account}] Share")
    time.sleep(1)

def repost_post(device_id, account):
    print(f"[{device_id}] [{account}] Repost")
    time.sleep(1)

def share_to_story(device_id, account):
    print(f"[{device_id}] [{account}] Share to Story")
    time.sleep(1)


ACTION_EXECUTORS = {
    "like": like_post,
    "comment": comment_post,
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
        # fallback for testing
        return ["acc_1", "acc_2", "acc_3"]

    with open(path, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]


# =========================
# MAIN DEVICE WORKER
# =========================
def device_worker(device_id):
    print(f"\n[{device_id}] Worker started")

    # -------------------------
    # STEP 5: Resume checkpoint
    # -------------------------
    checkpoint = load_checkpoint(device_id)

    # -------------------------
    # STEP 6: InfluensorOS Splash
    # -------------------------
    show_splash(10)

    # -------------------------
    # STEP 7: Load customers
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
    # STEP 8–9: Pick or Resume
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
            "step_index": 0
        })

        print(f"[{device_id}] Selected {customer['customer_id']} | {post}")

    # -------------------------
    # STEP 10: Account Loop
    # -------------------------
    accounts = load_accounts(device_id)

    for ai in range(account_index, len(accounts)):
        account = accounts[ai]
        print(f"[{device_id}] Switching account → {account}")

        open_instagram(device_id)
        open_profile_by_username(device_id, customer["username"])
        open_post_by_url(device_id, post)

        actions = build_actions(customer)
        if customer["settings"].get("randomize_action_sequence"):
            random.shuffle(actions)

        for si in range(step_index, len(actions)):
            action = actions[si]
            executor = ACTION_EXECUTORS.get(action)

            if executor:
                executor(device_id, account)

            save_checkpoint(device_id, {
                "customer_id": customer["customer_id"],
                "post": post,
                "account_index": ai,
                "step_index": si + 1
            })

        step_index = 0

        save_checkpoint(device_id, {
            "customer_id": customer["customer_id"],
            "post": post,
            "account_index": ai + 1,
            "step_index": 0
        })

        time.sleep(ACCOUNT_COOLDOWN)

    # -------------------------
    # STEP 11: Demo accounting
    # -------------------------
    if customer.get("type") == "demo":
        mark_demo_post_done(customer, device_id)

    clear_checkpoint(device_id)
    print(f"[{device_id}] Cycle completed for {customer['customer_id']}")

    time.sleep(CYCLE_COOLDOWN)
