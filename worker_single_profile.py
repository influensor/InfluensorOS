"""Standalone InfluensorOS worker with configurable device concurrency and account-switch limits.
Does not modify worker.py or other engine files. Scheduling state is in memory."""

import os
import random
import threading
import time

from engine.logger import info, warn, error
from engine.config import DELIVERY_DIR
from engine.utils.file_utils import safe_json_load

# Existing engine logic (read-only reuse)
from engine.logic.post_loader import load_posts
from engine.logic.demo_guard import demo_allowed, mark_demo_post_done
from engine.logic.checkpoint_manager import (
    load as load_checkpoint,
    save as save_checkpoint,
    clear as clear_checkpoint,
)
from engine.logic.comment_loader import load_random_comment
from engine.logic.delivery_tracker import (
    mark_post_delivered,
    account_already_done,
    device_already_done,
)
from engine.logic.rate_limiter import can_perform, record_action
from engine.logic.execution_window import enforce_execution_window
from engine.logic.device_caps import device_can_perform, record_device_action
from engine.logic.device_status import get_expected_accounts
from engine.logic.remote_config import get_config, kill_switch_active
from engine.logic.customer_cycle import (
    get_next_customer,
    mark_customer_completed,
    load_cycle,
)

# Existing UI actions
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
from engine.ui.gif import post_gif_comment
from engine.ui.repost import repost_post as ui_repost_post
from engine.ui.share import share_post as ui_share_post
from engine.ui.save import save_post as ui_save_post
from engine.ui.interested import mark_post_interested
from engine.ui.switch_account import switch_account
from engine.ui.add_to_story import add_to_story




# ============================================================
# LOCAL CONFIGURATION — EDIT THIS SECTION ONLY
# ============================================================
# No customer JSON files are loaded by this worker.
# `customer_id` must match the filename stem used by your existing
# post file: data/posts/<customer_id>.json, and existing delivery state.
# If your current data uses the Instagram username as the customer ID,
# set customer_id equal to username.
#
# Supported actions (same action set as the main worker):
# like, comment, gif_comment, save, share, repost, interested, add_to_story
# Story-view/like remains part of the existing navigation flow, as in worker.py.
#
# Add one dictionary per target Instagram profile. Use enabled=False to
# temporarily disable a profile without deleting its configuration.
TARGET_PROFILES = [
    # Example — replace values and uncomment to enable:
     {
         "enabled": True,
         "username": "women_communityy_",
         "customer_id": "women_communityy_",
         "type": "paid",
         "plan_type": "multi_post_per_day",
         "start_date": "2026-10-12",
         "actions": ["like", "comment", "save", "share","repost", "interested"],
         "randomize_action_sequence": True,
     }
]

SUPPORTED_ACTIONS = {"like", "comment", "save", "share","repost", "interested"}


# ----------------------------
# Tunables
# ----------------------------
ACCOUNT_COOLDOWN = 3
CYCLE_COOLDOWN = 30
IDLE_RETRY_SECONDS = 5

MAX_ACCOUNT_SWITCHES_MIN = 5
MAX_ACCOUNT_SWITCHES_MAX = 5

# Number of top-most eligible (not-yet-delivered) posts to select for EACH
# TARGET_PROFILE on EACH device during this script run. The quota is random.
MIN_POSTS_PER_ACCOUNT_PER_DEVICE = 2
MAX_POSTS_PER_ACCOUNT_PER_DEVICE = 5
MAX_SIMULTANEOUS_DEVICES = 5

# YES: do not let two active devices process the same source account at once.
# NO: source-account overlap across devices is allowed.
UNIQUE_ACCOUNT_PER_DEVICE = False

_ACTIVE_SOURCE_ACCOUNTS = set()
_ACTIVE_SOURCE_ACCOUNTS_LOCK = threading.Lock()

# In-memory TARGET_PROFILE post quota state; resets when this script restarts.
# Each (device, target profile) gets a random quota and the top-most eligible
# undelivered posts up to that quota.
_TARGET_PROFILE_POST_QUOTAS = {}  # (device_id, customer_id) -> {limit, posts, completed}
_TARGET_PROFILE_QUOTA_LOCK = threading.Lock()


def _target_profile_key(device_id, customer):
    return (str(device_id), str(customer.get("customer_id")))


def _get_target_profile_post_batch(device_id, customer):
    """Choose a random quota of top-most eligible, not-yet-delivered posts once."""
    key = _target_profile_key(device_id, customer)
    with _TARGET_PROFILE_QUOTA_LOCK:
        record = _TARGET_PROFILE_POST_QUOTAS.get(key)
        if record is not None:
            return record

    # The shared load_posts() helper returns only ONE incomplete post. Here we
    # intentionally load the whole target-post list so we can select the top N
    # incomplete posts in the file's existing newest-to-oldest order.
    posts_path = os.path.join("data", "posts", f"{customer['customer_id']}.json")
    all_posts = safe_json_load(posts_path, [])
    if not isinstance(all_posts, list):
        all_posts = []

    delivery_path = os.path.join(
        DELIVERY_DIR, str(device_id), f"{customer['customer_id']}.json"
    )
    delivery = safe_json_load(delivery_path, {"posts": {}})
    delivery_posts = delivery.get("posts", {}) if isinstance(delivery, dict) else {}
    if not isinstance(delivery_posts, dict):
        delivery_posts = {}

    available = []
    for post in all_posts:
        if not isinstance(post, dict) or not post.get("url") or not post.get("shortcode"):
            continue
        delivery_record = delivery_posts.get(post["url"], {})
        completed = (
            bool(delivery_record.get("completed", False))
            if isinstance(delivery_record, dict)
            else False
        )
        if not completed:
            available.append(post)
    low = max(1, int(MIN_POSTS_PER_ACCOUNT_PER_DEVICE))
    high = max(low, int(MAX_POSTS_PER_ACCOUNT_PER_DEVICE))
    quota = random.randint(low, high)
    selected = available[:quota]
    record = {
        "limit": len(selected),
        "requested_limit": quota,
        "posts": selected,
        "completed": set(),
    }
    with _TARGET_PROFILE_QUOTA_LOCK:
        # Another thread should not own this same device/profile, but preserve
        # the first assignment if initialization races.
        existing = _TARGET_PROFILE_POST_QUOTAS.setdefault(key, record)
        record = existing

    info(
        f"Target profile @{customer.get('username')} on device {device_id}: "
        f"selected {record['limit']} top eligible post(s) "
        f"(random quota={record['requested_limit']})",
        device_id,
    )
    return record


def _record_target_profile_post_completed(device_id, customer, post):
    key = _target_profile_key(device_id, customer)
    url = str(post.get("url") or "")
    with _TARGET_PROFILE_QUOTA_LOCK:
        record = _TARGET_PROFILE_POST_QUOTAS.get(key)
        if record is None:
            return True, 0, 0
        record["completed"].add(url)
        done = len(record["completed"])
        limit = record["limit"]
        return done >= limit, done, limit


# ----------------------------
# Target-profile selection (no profile locks)
# ----------------------------
class ProfileLease:
    """Compatibility shim: profile locking is intentionally disabled."""
    def __init__(self, customer, device_id):
        self.customer = customer
        self.device_id = str(device_id)
    def acquire(self):
        return True
    def release(self):
        return None


def _profile_lease(customer, device_id):
    return ProfileLease(customer, device_id)


# ----------------------------
# Action executors (same registry as main worker)
# ----------------------------
def _open_profile(device_id, account, customer):
    info(f"[{account}] Open target profile @{customer['username']}", device_id)
    return ui_open_profile_by_username(device_id, customer["username"])


def _like(device_id, account):
    return ui_like_post(device_id)


def _comment(device_id, account, customer, post):
    comment = load_random_comment(
        customer_id=customer["customer_id"],
        shortcode=post.get("shortcode"),
    )
    if not comment:
        warn("No comment available; skipping comment action", device_id)
        return False
    return post_comment(device_id, comment)


def _gif_comment(device_id, account):
    return post_gif_comment(device_id)


def _save(device_id, account):
    return ui_save_post(device_id)


def _share(device_id, account):
    return ui_share_post(device_id)


def _repost(device_id, account):
    return ui_repost_post(device_id)


def _interested(device_id, account):
    return mark_post_interested(device_id)


def _add_to_story(device_id, account):
    return add_to_story(device_id)


ACTION_EXECUTORS = {
    "like": _like,
    "comment": _comment,
    "gif_comment": _gif_comment,
    "save": _save,
    "share": _share,
    "repost": _repost,
    "interested": _interested,
    "add_to_story": _add_to_story,
}


def _eligible_customers(device_id):
    """Build runtime customer records from TARGET_PROFILES; never read customer files."""
    eligible = []
    seen_ids = set()

    for configured in TARGET_PROFILES:
        if not isinstance(configured, dict) or not configured.get("enabled", True):
            continue

        username = str(configured.get("username") or "").strip().lstrip("@")
        customer_id = str(configured.get("customer_id") or "").strip()
        if not username or not customer_id:
            warn("Skipping profile config: both username and customer_id are required", device_id)
            continue
        if customer_id in seen_ids:
            warn(f"Duplicate customer_id in TARGET_PROFILES: {customer_id}; skipping duplicate", device_id)
            continue
        seen_ids.add(customer_id)

        action_list = configured.get("actions", [])
        if not isinstance(action_list, list):
            warn(f"Actions must be a list for @{username}; profile skipped", device_id)
            continue
        unknown = [action for action in action_list if action not in SUPPORTED_ACTIONS]
        if unknown:
            warn(f"Unsupported actions for @{username}: {unknown}; they will be ignored", device_id)
        actions = [action for action in action_list if action in SUPPORTED_ACTIONS]

        # action_registry.build() is intentionally bypassed: actions are defined
        # directly in this file, then represented in the settings shape expected
        # by the existing main-worker action flow.
        settings = {action: action in actions for action in SUPPORTED_ACTIONS}
        settings["randomize_action_sequence"] = bool(
            configured.get("randomize_action_sequence", False)
        )

        customer = {
            "customer_id": customer_id,
            "username": username,
            "type": configured.get("type", "paid"),
            "plan": {"type": configured.get("plan_type", "multi_post_per_day")},
            "settings": settings,
            "demo_control": configured.get("demo_control"),
        }

        if customer["type"] == "demo" and not demo_allowed(customer, device_id):
            continue
        eligible.append(customer)

    return eligible


def _customer_by_id(customers, customer_id):
    return next(
        (c for c in customers if str(c.get("customer_id")) == str(customer_id)),
        None,
    )


def _pick_customer_with_available_lock(device_id, customers, checkpoint):
    """Select/resume a target profile without acquiring a profile lock."""
    if checkpoint.get("customer_id"):
        resumed = _customer_by_id(customers, checkpoint["customer_id"])
        if resumed:
            return resumed, ProfileLease(resumed, device_id), True
        clear_checkpoint(device_id)
        checkpoint = {}

    if not customers:
        return None, None, False
    eligible_ids = [c["customer_id"] for c in customers]
    first_id = get_next_customer(device_id, eligible_ids)
    ordered_ids = [first_id] + [cid for cid in eligible_ids if str(cid) != str(first_id)]
    for customer_id in ordered_ids:
        customer = _customer_by_id(customers, customer_id)
        if customer:
            return customer, ProfileLease(customer, device_id), False
    return None, None, False


def _load_customer_post(device_id, customer, checkpoint, resumed):
    # Resume the exact in-progress post first; its target-profile quota is
    # counted only after this post reaches completion.
    if resumed:
        post = checkpoint.get("post")
        if isinstance(post, dict) and post.get("url") and post.get("shortcode"):
            info(
                f"Resuming same post {post['shortcode']} for @{customer.get('username')}",
                device_id,
            )
            return post

    record = _get_target_profile_post_batch(device_id, customer)
    completed_urls = record["completed"]
    for post in record["posts"]:
        if str(post.get("url")) not in completed_urls:
            return post
    return None


def _save_worker_checkpoint(device_id, customer, post, account_index, active_account):
    save_checkpoint(
        device_id,
        {
            "customer_id": customer["customer_id"],
            "post": post,
            "account_index": account_index,
            "active_account": active_account,
            "target_username": customer.get("username"),
            "updated_at": int(time.time()),
        },
    )


def _process_customer(device_id, customer, post, checkpoint, resumed):
    profile_type = "demo" if customer.get("type") == "demo" else "paid"
    rate_limits = get_config("limits", {}).get(profile_type, {})
    execution_window = get_config("execution_window", {}).get(profile_type, {})
    device_caps = get_config("device_caps", {}).get(profile_type, {})

    enforce_execution_window(execution_window, device_id)

    account_index = int(checkpoint.get("account_index", 0)) if resumed else 0
    active_account = checkpoint.get("active_account") if resumed else None
    max_account_switches = random.randint(
        MAX_ACCOUNT_SWITCHES_MIN, MAX_ACCOUNT_SWITCHES_MAX
    )
    switches_this_post = 0
    any_delivery_marked = False

    info(
        f"Processing customer={customer['customer_id']} target=@{customer.get('username')} "
        f"post={post.get('shortcode')} account_cap={max_account_switches}",
        device_id,
    )

    if not open_instagram(device_id):
        warn("Could not open Instagram; retaining checkpoint for retry", device_id)
        return False

    # IMPORTANT: keep this exact post active until the configured account-switch
    # count has been executed. Do not exit early because delivery tracking says
    # the post is complete; only a missing account from switch_account can end it.
    while switches_this_post < max_account_switches:
        # An account restored from a checkpoint is processed before switching.
        if not active_account:
            next_account = switch_account(device_id)
            if not next_account:
                warn("Account switcher returned no account; ending this customer pass", device_id)
                break
            active_account = next_account
            switches_this_post += 1
            account_key = str(active_account).strip().lstrip("@").lower()
            if UNIQUE_ACCOUNT_PER_DEVICE:
                with _ACTIVE_SOURCE_ACCOUNTS_LOCK:
                    if account_key in _ACTIVE_SOURCE_ACCOUNTS:
                        warn(f"Source account {active_account} is already active on another device; counting this switch and trying another account", device_id)
                        active_account = None
                        account_index += 1
                        _save_worker_checkpoint(device_id, customer, post, account_index, active_account)
                        continue
                    _ACTIVE_SOURCE_ACCOUNTS.add(account_key)
            _save_worker_checkpoint(
                device_id, customer, post, account_index, active_account
            )
            # Give Instagram time to finish switching accounts before navigation.
            time.sleep(ACCOUNT_COOLDOWN)

        info(f"Using source account: {active_account}", device_id)

        # Match the original worker.py behavior: do not skip an account merely
        # because delivery tracking already records it. Continue attempting the
        # configured actions on this same post until the account-switch cap ends.

        try:
            profile_open_result = _open_profile(device_id, active_account, customer)
            # Some UI helpers perform navigation but return None; only an explicit
            # False should be treated as a navigation failure.
            if profile_open_result is False:
                warn(f"Could not open target profile @{customer.get('username')}", device_id)
                active_account = None
                account_index += 1
                _save_worker_checkpoint(
                    device_id, customer, post, account_index, active_account
                )
                time.sleep(ACCOUNT_COOLDOWN)
                continue

            # Keep the current worker's story-view/like step.
            story_view_like(device_id)

            post_open_result = open_post_by_url(device_id, post, customer["username"])
            # Match main worker behavior: don't treat a None return as failure.
            if post_open_result is False:
                warn(f"Could not open post {post.get('shortcode')}; no delivery recorded", device_id)
                active_account = None
                account_index += 1
                _save_worker_checkpoint(
                    device_id, customer, post, account_index, active_account
                )
                time.sleep(ACCOUNT_COOLDOWN)
                continue

            action_performed = False
            already_liked = should_skip_actions(device_id)

            if already_liked:
                # Preserve main worker behavior: view the already-liked post and
                # count this account as delivered without repeating other actions.
                view_post(device_id, 1, random.randint(10, 90))
            else:
                settings = customer.get("settings") or {}
                actions = [
                    action for action in ACTION_EXECUTORS
                    if settings.get(action, False)
                ]
                if settings.get("randomize_action_sequence"):
                    random.shuffle(actions)

                for action in actions:
                    if not device_can_perform(device_id, action, device_caps):
                        continue
                    if not can_perform(device_id, active_account, action, rate_limits):
                        continue
                    if action == "comment":
                        success = _comment(device_id, active_account, customer, post)
                    else:
                        success = ACTION_EXECUTORS[action](device_id, active_account)

                    if success:
                        action_performed = True
                        record_action(device_id, active_account, action)
                        record_device_action(device_id, action)

            if already_liked or action_performed:
                expected_accounts = max(1, int(get_expected_accounts(device_id) or 0))
                mark_post_delivered(
                    customer["customer_id"],
                    post["url"],
                    device_id,
                    active_account,
                    expected_accounts=expected_accounts,
                    customer_type=profile_type,
                )
                any_delivery_marked = True
            else:
                info(
                    f"No action succeeded for account {active_account}; delivery not marked",
                    device_id,
                )

        except Exception as exc:
            error(f"Action/navigation error for account {active_account}: {exc}", device_id)
            # Preserve the checkpoint with the active account so this work can
            # be resumed/debugged rather than silently declaring it complete.
            _save_worker_checkpoint(
                device_id, customer, post, account_index, active_account
            )
            if UNIQUE_ACCOUNT_PER_DEVICE:
                account_key = str(active_account or "").strip().lstrip("@").lower()
                if account_key:
                    with _ACTIVE_SOURCE_ACCOUNTS_LOCK:
                        _ACTIVE_SOURCE_ACCOUNTS.discard(account_key)
            raise
        finally:
            # Account switching happens only after the current account's work
            # and delivery-tracking decision have finished.
            pass

        if UNIQUE_ACCOUNT_PER_DEVICE:
            account_key = str(active_account or "").strip().lstrip("@").lower()
            if account_key:
                with _ACTIVE_SOURCE_ACCOUNTS_LOCK:
                    _ACTIVE_SOURCE_ACCOUNTS.discard(account_key)
        active_account = None
        account_index += 1
        _save_worker_checkpoint(
            device_id, customer, post, account_index, active_account
        )
        time.sleep(ACCOUNT_COOLDOWN)

    post_completed = device_already_done(
        customer["customer_id"], post["url"], device_id
    )

    if profile_type == "demo" and post_completed and any_delivery_marked:
        mark_demo_post_done(customer, device_id)

    if post_completed:
        # Count completed POSTS against the TARGET_PROFILE quota (not source
        # account quotas). Continue this target profile until its selected
        # top-post batch is complete.
        quota_done, quota_completed, quota_limit = _record_target_profile_post_completed(
            device_id, customer, post
        )
        clear_checkpoint(device_id)
        if quota_done:
            mark_customer_completed(device_id, customer["customer_id"])
            info(
                f"Target profile @{customer.get('username')} finished its selected "
                f"post quota ({quota_completed}/{quota_limit}); moving to another target profile",
                device_id,
            )
        else:
            info(
                f"Target profile @{customer.get('username')} completed post "
                f"{post.get('shortcode')} ({quota_completed}/{quota_limit}); "
                "more selected posts remain for this target profile",
                device_id,
            )
    else:
        # Account-switch cap ended this pass before the post was complete.
        # Keep the same customer + post in the checkpoint so the next outer
        # loop continues this post rather than advancing through the post list.
        _save_worker_checkpoint(
            device_id, customer, post, account_index, active_account=None
        )
        info(
            f"Post still incomplete; keeping same post for next loop: "
            f"{customer['customer_id']} / {post.get('shortcode')}",
            device_id,
        )

    time.sleep(CYCLE_COOLDOWN)
    return post_completed


def _device_job_complete(device_id, customers):
    """Return True once this device has completed its random post batch for every target profile."""
    all_done = True
    for customer in customers:
        record = _get_target_profile_post_batch(device_id, customer)
        with _TARGET_PROFILE_QUOTA_LOCK:
            done = len(record["completed"])
            limit = int(record["limit"])
        # A profile with zero eligible posts is complete for this device's job.
        if done < limit:
            all_done = False
    return all_done


def device_worker(device_id, max_cycles=None):
    """Run continuously. max_cycles is optional for testing; None means forever."""
    info("Independent single-profile worker started", device_id)
    enabled, message = kill_switch_active()
    if enabled:
        error(f"KILL SWITCH ACTIVE: {message}", device_id)
        return

    show_splash(1)
    completed_cycles = 0

    while max_cycles is None or completed_cycles < max_cycles:
        enabled, message = kill_switch_active()
        if enabled:
            error(f"KILL SWITCH ACTIVE: {message}", device_id)
            return

        customers = _eligible_customers(device_id)
        if not customers:
            warn("No eligible customers; this device has no target profiles to process", device_id)
            return

        # Initialize a fresh random post batch for every TARGET_PROFILE on this
        # device. Once every batch is complete, this device's job ends so the
        # coordinator can launch the next available device.
        if _device_job_complete(device_id, customers):
            info("All TARGET_PROFILES completed on this device; releasing slot for the next device", device_id)
            return

        checkpoint = load_checkpoint(device_id) or {}
        customer, lease, resumed = _pick_customer_with_available_lock(
            device_id, customers, checkpoint
        )

        if not customer or not lease:
            time.sleep(IDLE_RETRY_SECONDS)
            continue

        try:
            # Lease remains held for post selection, account loop, all actions,
            # delivery updates and checkpoint cleanup for this target profile.
            post = _load_customer_post(device_id, customer, checkpoint, resumed)
            if not post:
                info(
                    f"No remaining selected undelivered posts for target profile "
                    f"@{customer.get('username')}; marking profile visited",
                    device_id,
                )
                mark_customer_completed(device_id, customer["customer_id"])
                clear_checkpoint(device_id)
                completed_cycles += 1
                time.sleep(1)
                continue

            _save_worker_checkpoint(
                device_id,
                customer,
                post,
                checkpoint.get("account_index", 0) if resumed else 0,
                checkpoint.get("active_account") if resumed else None,
            )
            _process_customer(device_id, customer, post, checkpoint, resumed)
            completed_cycles += 1

        except Exception as exc:
            error(f"Customer pass failed; checkpoint retained when possible: {exc}", device_id)
            # Keep failures isolated to this pass; retry on a later loop.
            time.sleep(IDLE_RETRY_SECONDS)
        finally:
            lease.release()


def run_workers(device_ids, max_cycles_per_device=None):
    """Run up to MAX_SIMULTANEOUS_DEVICES at once; start the next device when a slot frees."""
    from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

    devices = list(dict.fromkeys(str(d) for d in device_ids))
    if not devices:
        warn("No authorized devices supplied")
        return

    concurrency = max(1, min(int(MAX_SIMULTANEOUS_DEVICES), len(devices)))
    info(
        f"Starting target-profile job queue: devices={len(devices)}, "
        f"max_simultaneous_devices={concurrency}, "
        f"unique_account_per_device={UNIQUE_ACCOUNT_PER_DEVICE}, "
        f"account_switch_limit={MAX_ACCOUNT_SWITCHES_MIN}-{MAX_ACCOUNT_SWITCHES_MAX}, "
        f"target_posts_per_profile_per_device={MIN_POSTS_PER_ACCOUNT_PER_DEVICE}-{MAX_POSTS_PER_ACCOUNT_PER_DEVICE}"
    )

    # A device runs the same configured TARGET_PROFILES with fresh per-device
    # random post quotas. As soon as it completes all profiles, the next device
    # in the queue is started; no more than `concurrency` run simultaneously.
    next_index = 0
    active = {}
    with ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix="influensor-device") as pool:
        while next_index < len(devices) and len(active) < concurrency:
            device_id = devices[next_index]
            next_index += 1
            active[pool.submit(device_worker, device_id, max_cycles_per_device)] = device_id

        while active:
            done, _ = wait(active, return_when=FIRST_COMPLETED)
            for future in done:
                device_id = active.pop(future)
                try:
                    future.result()
                    info(f"Device {device_id} finished its target-profile job", device_id)
                except Exception as exc:
                    error(f"Device worker crashed: {exc}", device_id)

                if next_index < len(devices):
                    next_device = devices[next_index]
                    next_index += 1
                    info(f"Assigning next device {next_device} to the same job with fresh random target-post quotas", next_device)
                    active[pool.submit(device_worker, next_device, max_cycles_per_device)] = next_device

    info("All connected devices have completed their target-profile job queue")


if __name__ == "__main__":
    from engine.logic.device_auth import get_authorized_devices

    devices = get_authorized_devices()
    if not devices:
        print("No authorized ADB devices connected.")
    else:
        print(f"Starting independent worker on {len(devices)} device(s): {devices}")
        run_workers(devices)
