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
from engine.logic.delivery_tracker import mark_post_delivered

# Rate / control
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
    open_profile_by_username,
    open_post_by_url,
)
from engine.ui.actions import should_skip_actions
from engine.ui.view import view_post
from engine.ui.like import like_post as ui_like_post
from engine.ui.comment import post_comment
from engine.ui.save import save_post as ui_save_post
from engine.ui.share import share_post as ui_share_post
from engine.ui.repost import repost_post as ui_repost_post

# =========================
# CONFIG
# =========================
ACCOUNT_COOLDOWN = 3
CYCLE_COOLDOWN = 5


# =========================
# ACTION WRAPPERS
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
    "comment": comment_post,
    "save": save_post,
    "share": share_post,
    "repost": repost_post,
}


# =========================
# MAIN WORKER
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

    # -------------------------
    # Splash
    # -------------------------
    show_splash(10)

    # -------------------------
    # Resume checkpoint
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
        time.sleep(60)
        return

    # -------------------------
    # Select / Resume
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
    # Remote config
    # -------------------------
    profile = "demo" if customer.get("type") == "demo" else "paid"

    rate_limits = get_config("limits", {}).get(profile, {})
    action_probability = get_config("probability", {}).get(profile, {})
    execution_window = get_config("execution_window", {}).get(profile, {})
    device_caps = get_config("device_caps", {}).get(profile, {})

    enforce_execution_window(execution_window, device_id)

    # -------------------------
    # Accounts loop
    # -------------------------
    accounts = customer.get("accounts", ["acc_1", "acc_2", "acc_3"])

    for ai in range(account_index, len(accounts)):
        account = accounts[ai]
        print(f"[{device_id}] Switching account → {account}")

        # Navigation
        open_instagram(device_id)
        time.sleep(2)

        open_profile_by_username(device_id, customer["username"])
        time.sleep(3)

        open_post_by_url(device_id, post)
        time.sleep(3)

        # -------------------------
        # DECISION GATE
        # -------------------------
        if should_skip_actions(device_id):
            print(f"[{device_id}] [{account}] Post already liked → view only")

            view_post(device_id, 1, 60)

            # ✅ MARK DELIVERY EVEN ON SKIP
            mark_post_delivered(
                customer_id=customer["customer_id"],
                post_url=post,
                device_id=device_id
            )

            save_checkpoint(device_id, {
                "customer_id": customer["customer_id"],
                "post": post,
                "account_index": ai + 1,
                "step_index": 0,
            })
            continue

        # -------------------------
        # Execute actions
        # -------------------------
        actions = build_actions(customer)

        if customer["settings"].get("randomize_action_sequence"):
            random.shuffle(actions)

        for si in range(step_index, len(actions)):
            action = actions[si]

            if not device_can_perform(device_id, action, device_caps):
                continue

            if not can_perform(device_id, account, action, rate_limits):
                continue

            if not should_perform(action, action_probability):
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
    # Demo accounting
    # -------------------------
    if customer.get("type") == "demo":
        mark_demo_post_done(customer, device_id)

    clear_checkpoint(device_id)
    print(f"[{device_id}] Cycle completed for {customer['customer_id']}")

    time.sleep(CYCLE_COOLDOWN)
