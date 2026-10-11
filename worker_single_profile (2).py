"""Independent InfluensorOS worker with run-wide source-account scheduling.

This file reuses the existing InfluensorOS engine modules and does not modify
worker.py or any other existing project file. It runs at most
MAX_SIMULTANEOUS_DEVICES devices concurrently and assigns each source account
once per Python process.
"""


import json
import os
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from engine.logger import info, warn, error

# Existing engine logic (read-only reuse)
from engine.logic.post_loader import load_posts
from engine.logic.demo_guard import demo_allowed, mark_demo_post_done
from engine.logic.checkpoint_manager import (
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
from engine.logic.device_status import get_expected_accounts, get_accounts
from engine.logic.remote_config import get_config, kill_switch_active

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
         "actions": ["like", "comment", "save", "share","repost", "interested"],
         "randomize_action_sequence": True,
     },
     {
         "enabled": True,
         "username": "berlycanek",
         "customer_id": "berlycanek",
         "type": "paid",
         "plan_type": "multi_post_per_day",
         "actions": ["like", "comment", "save", "share","repost", "interested"],
         "randomize_action_sequence": True,
     }
]

SUPPORTED_ACTIONS = {
    "like", "comment", "gif_comment", "save", "share", "repost", "interested", "add_to_story",}


# ----------------------------
# Tunables
# ----------------------------
MAX_SIMULTANEOUS_DEVICES = 2
MIN_POSTS_PER_ACCOUNT_PER_DEVICE = 1
MAX_POSTS_PER_ACCOUNT_PER_DEVICE = 5
ACCOUNT_COOLDOWN = 3
CYCLE_COOLDOWN = 600
MAX_ACCOUNT_DISCOVERY_ATTEMPTS = 50

# All scheduling state is intentionally in memory. Restarting Python resets it.
_RUN_STATE_LOCK = threading.Lock()
_CLAIMED_SOURCE_ACCOUNTS = {}  # normalized account -> device ID
_COMPLETED_SOURCE_ACCOUNTS = set()
_FAILED_SOURCE_ACCOUNTS = {}   # normalized account -> error string
_ACCOUNT_POST_USAGE = {}       # normalized account -> {posts, limit}
_ACCOUNT_POST_USAGE_LOCK = threading.Lock()
_ACCOUNT_ATTEMPTED_POSTS = set()  # (account, customer_id, post_url)
_ACCOUNT_ATTEMPTED_POSTS_LOCK = threading.Lock()


def _account_usage_key(account):
    if isinstance(account, dict):
        account = (
            account.get("username")
            or account.get("account")
            or account.get("name")
            or account.get("id")
            or str(account)
        )
    return str(account or "").strip().lstrip("@").lower()


def _claim_source_account(account, device_id):
    """Atomically assign a source account to only one device for this run."""
    key = _account_usage_key(account)
    if not key:
        return False
    with _RUN_STATE_LOCK:
        if key in _CLAIMED_SOURCE_ACCOUNTS or key in _COMPLETED_SOURCE_ACCOUNTS:
            return False
        _CLAIMED_SOURCE_ACCOUNTS[key] = str(device_id)
        info(f"Assigned source account={key} to device={device_id}", device_id)
        return True


def _finish_source_account(account, device_id, failure=None):
    key = _account_usage_key(account)
    if not key:
        return
    with _RUN_STATE_LOCK:
        _CLAIMED_SOURCE_ACCOUNTS.pop(key, None)
        _COMPLETED_SOURCE_ACCOUNTS.add(key)
        if failure:
            _FAILED_SOURCE_ACCOUNTS[key] = str(failure)
    if failure:
        warn(
            f"Source account={key} finished with an error on device={device_id}: {failure}",
            device_id,
        )
    else:
        info(f"Source account={key} is finished for this script run", device_id)


def _account_post_budget(device_id, account):
    """Return (successful_posts, random_limit); quota is global per account/run."""
    account_key = _account_usage_key(account)
    if not account_key:
        return 0, max(1, int(MAX_POSTS_PER_ACCOUNT_PER_DEVICE))
    with _ACCOUNT_POST_USAGE_LOCK:
        record = _ACCOUNT_POST_USAGE.get(account_key)
        if record is None:
            low = max(1, int(MIN_POSTS_PER_ACCOUNT_PER_DEVICE))
            high = max(low, int(MAX_POSTS_PER_ACCOUNT_PER_DEVICE))
            record = {"posts": 0, "limit": random.randint(low, high)}
            _ACCOUNT_POST_USAGE[account_key] = record
            info(
                f"Random post quota assigned: account={account_key} "
                f"device={device_id} quota={record['limit']}",
                device_id,
            )
        return record["posts"], record["limit"]


def _record_account_post(device_id, account):
    account_key = _account_usage_key(account)
    if not account_key:
        return
    with _ACCOUNT_POST_USAGE_LOCK:
        record = _ACCOUNT_POST_USAGE.get(account_key)
        if record is None:
            low = max(1, int(MIN_POSTS_PER_ACCOUNT_PER_DEVICE))
            high = max(low, int(MAX_POSTS_PER_ACCOUNT_PER_DEVICE))
            record = {"posts": 0, "limit": random.randint(low, high)}
            _ACCOUNT_POST_USAGE[account_key] = record
        record["posts"] += 1
        posts, limit = record["posts"], record["limit"]
    info(
        f"Source account post quota: account={account_key} "
        f"posts={posts}/{limit}",
        device_id,
    )


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


def _candidate_posts_for_account(device_id, customer, account):
    """Use the existing post loader, then scan later posts if this account handled its first result."""
    customer_id = customer["customer_id"]

    # Preserve the normal loader's selection rules and ordering first.
    loaded = load_posts(customer, device_id) or []
    if loaded:
        first = loaded[0]
        if (
            isinstance(first, dict)
            and first.get("url")
            and first.get("shortcode")
            and not account_already_done(customer_id, first["url"], device_id, account)
        ):
            key = (_account_usage_key(account), str(customer_id), str(first["url"]))
            with _ACCOUNT_ATTEMPTED_POSTS_LOCK:
                attempted = key in _ACCOUNT_ATTEMPTED_POSTS
            if not attempted:
                return [first]

    # If the loader's first incomplete post was already handled by this account,
    # scan the same post file for the next eligible item instead of repeating it.
    path = os.path.join("data", "posts", f"{customer_id}.json")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            posts = json.load(handle)
    except FileNotFoundError:
        return []
    except Exception as exc:
        warn(f"Could not read posts for {customer_id}: {exc}", device_id)
        return []

    if not isinstance(posts, list):
        return []

    candidates = []
    account_key = _account_usage_key(account)
    for post in posts:
        if not isinstance(post, dict) or not post.get("url") or not post.get("shortcode"):
            continue
        post_url = post["url"]
        if device_already_done(customer_id, post_url, device_id):
            continue
        if account_already_done(customer_id, post_url, device_id, account):
            continue
        with _ACCOUNT_ATTEMPTED_POSTS_LOCK:
            if (account_key, str(customer_id), str(post_url)) in _ACCOUNT_ATTEMPTED_POSTS:
                continue
        candidates.append(post)
    return candidates


def _mark_attempted_post(account, customer, post):
    key = (
        _account_usage_key(account),
        str(customer.get("customer_id")),
        str(post.get("url")),
    )
    with _ACCOUNT_ATTEMPTED_POSTS_LOCK:
        _ACCOUNT_ATTEMPTED_POSTS.add(key)


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


def _process_source_account(device_id, account, customers):
    """Use one assigned source account for its random quota of target posts."""
    account_key = _account_usage_key(account)
    posts_done, post_limit = _account_post_budget(device_id, account)
    profile_cursor = 0

    enabled, message = kill_switch_active()
    if enabled:
        raise RuntimeError(f"KILL SWITCH ACTIVE: {message}")
    if not open_instagram(device_id):
        raise RuntimeError("Could not open Instagram")

    while posts_done < post_limit:
        enabled, message = kill_switch_active()
        if enabled:
            raise RuntimeError(f"KILL SWITCH ACTIVE: {message}")

        candidate = None
        selected_customer = None
        if customers:
            # Rotate target profiles so one source account can serve different
            # configured profiles instead of repeatedly attempting one post.
            order = customers[profile_cursor:] + customers[:profile_cursor]
            for customer in order:
                posts = _candidate_posts_for_account(device_id, customer, account)
                if posts:
                    selected_customer = customer
                    candidate = posts[0]
                    profile_cursor = (customers.index(customer) + 1) % len(customers)
                    break

        if not candidate or not selected_customer:
            info(
                f"No more eligible target posts for source account={account_key}; "
                f"quota reached {posts_done}/{post_limit}",
                device_id,
            )
            break

        customer = selected_customer
        post = candidate
        profile_type = "demo" if customer.get("type") == "demo" else "paid"
        rate_limits = get_config("limits", {}).get(profile_type, {})
        execution_window = get_config("execution_window", {}).get(profile_type, {})
        device_caps = get_config("device_caps", {}).get(profile_type, {})
        enforce_execution_window(execution_window, device_id)

        _save_worker_checkpoint(device_id, customer, post, posts_done, account)
        info(
            f"Account work: source={account_key}, target=@{customer.get('username')}, "
            f"post={post.get('shortcode')}, quota={posts_done}/{post_limit}",
            device_id,
        )

        try:
            profile_open_result = _open_profile(device_id, account, customer)
            if profile_open_result is False:
                warn(f"Could not open target profile @{customer.get('username')}", device_id)
                _mark_attempted_post(account, customer, post)
                continue

            story_view_like(device_id)
            post_open_result = open_post_by_url(device_id, post, customer["username"])
            if post_open_result is False:
                warn(f"Could not open post {post.get('shortcode')}; no delivery recorded", device_id)
                _mark_attempted_post(account, customer, post)
                continue

            action_performed = False
            already_liked = should_skip_actions(device_id)
            if already_liked:
                view_post(device_id, 1, random.randint(10, 90))
            else:
                settings = customer.get("settings") or {}
                actions = [action for action in ACTION_EXECUTORS if settings.get(action, False)]
                if settings.get("randomize_action_sequence"):
                    random.shuffle(actions)

                for action in actions:
                    if not device_can_perform(device_id, action, device_caps):
                        continue
                    if not can_perform(device_id, account, action, rate_limits):
                        continue
                    if action == "comment":
                        success = _comment(device_id, account, customer, post)
                    else:
                        success = ACTION_EXECUTORS[action](device_id, account)
                    if success:
                        action_performed = True
                        record_action(device_id, account, action)
                        record_device_action(device_id, action)

            if already_liked or action_performed:
                expected_accounts = max(1, int(get_expected_accounts(device_id) or 0))
                mark_post_delivered(
                    customer["customer_id"],
                    post["url"],
                    device_id,
                    account,
                    expected_accounts=expected_accounts,
                    customer_type=profile_type,
                )
                _mark_attempted_post(account, customer, post)
                _record_account_post(device_id, account)
                posts_done, post_limit = _account_post_budget(device_id, account)

                if profile_type == "demo" and device_already_done(
                    customer["customer_id"], post["url"], device_id
                ):
                    mark_demo_post_done(customer, device_id)
            else:
                info(
                    f"No action succeeded for account={account_key} on "
                    f"{post.get('shortcode')}; this post will not be retried by this account this run",
                    device_id,
                )
                _mark_attempted_post(account, customer, post)

        except Exception as exc:
            error(
                f"Post action failed for source account={account_key}, "
                f"target=@{customer.get('username')}, post={post.get('shortcode')}: {exc}",
                device_id,
            )
            _mark_attempted_post(account, customer, post)
        finally:
            clear_checkpoint(device_id)
            time.sleep(CYCLE_COOLDOWN)

    posts_done, post_limit = _account_post_budget(device_id, account)
    info(
        f"Finished source account={account_key} on device={device_id}: "
        f"{posts_done}/{post_limit} posts handled",
        device_id,
    )


def device_worker(device_id):
    """Process each source account available on this device at most once per run."""
    info("Independent account-scheduler worker started", device_id)
    enabled, message = kill_switch_active()
    if enabled:
        error(f"KILL SWITCH ACTIVE: {message}", device_id)
        return

    show_splash(1)
    customers = _eligible_customers(device_id)
    if not customers:
        warn("No enabled target profiles configured", device_id)
        return

    registered_accounts = get_accounts(device_id) or []
    attempt_limit = min(
        MAX_ACCOUNT_DISCOVERY_ATTEMPTS,
        max(1, len(registered_accounts) + 1) if registered_accounts else MAX_ACCOUNT_DISCOVERY_ATTEMPTS,
    )
    seen_on_device = set()
    consecutive_repeats = 0

    for _ in range(attempt_limit):
        enabled, message = kill_switch_active()
        if enabled:
            error(f"KILL SWITCH ACTIVE: {message}", device_id)
            return

        try:
            account = switch_account(device_id)
        except Exception as exc:
            error(f"Could not switch source account: {exc}", device_id)
            return

        account_key = _account_usage_key(account)
        if not account_key:
            info("Account switcher returned no source account; device worker finished", device_id)
            break
        if account_key in seen_on_device:
            consecutive_repeats += 1
            known_count = len(set(_account_usage_key(a) for a in registered_accounts if _account_usage_key(a)))
            # With a registered inventory, stop only after every known account
            # has been observed. Without one, tolerate several repeated results
            # so a non-sequential account switcher can still reveal other accounts.
            if (known_count and len(seen_on_device) >= known_count) or consecutive_repeats >= 5:
                info(
                    f"Account cycle completed on device={device_id}; no new local accounts remain",
                    device_id,
                )
                break
            continue
        consecutive_repeats = 0
        seen_on_device.add(account_key)

        if not _claim_source_account(account, device_id):
            info(
                f"Skipping source account={account_key}; already assigned/completed on another worker",
                device_id,
            )
            continue

        failure = None
        try:
            _process_source_account(device_id, account, customers)
        except Exception as exc:
            failure = exc
            error(f"Source account={account_key} failed: {exc}", device_id)
        finally:
            _finish_source_account(account, device_id, failure)

        time.sleep(ACCOUNT_COOLDOWN)

    info(f"Device worker finished account discovery: device={device_id}", device_id)


def run_workers(device_ids, max_cycles_per_device=None):
    """Run no more than MAX_SIMULTANEOUS_DEVICES devices at the same time."""
    devices = list(dict.fromkeys(str(device_id) for device_id in device_ids))
    if not devices:
        warn("No authorized devices supplied")
        return

    concurrency = max(1, min(int(MAX_SIMULTANEOUS_DEVICES), len(devices)))
    info(
        f"Starting account scheduler: devices={len(devices)}, "
        f"max_simultaneous_devices={concurrency}, "
        f"target_profiles={sum(1 for p in TARGET_PROFILES if isinstance(p, dict) and p.get('enabled', True))}"
    )

    with ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix="influensor-device") as pool:
        futures = {pool.submit(device_worker, device_id): device_id for device_id in devices}
        for future in as_completed(futures):
            device_id = futures[future]
            try:
                future.result()
            except Exception as exc:
                error(f"Device worker crashed: {exc}", device_id)

    with _RUN_STATE_LOCK:
        completed = sorted(_COMPLETED_SOURCE_ACCOUNTS)
        failed = dict(_FAILED_SOURCE_ACCOUNTS)
    info(
        f"Account scheduler finished. Unique accounts processed={len(completed)}, "
        f"failed={len(failed)}"
    )
    if failed:
        warn(f"Accounts that ended with errors: {failed}")


if __name__ == "__main__":
    from engine.logic.device_auth import get_authorized_devices

    devices = get_authorized_devices()
    if not devices:
        print("No authorized ADB devices connected.")
    else:
        print(f"Starting account scheduler on {len(devices)} device(s); max simultaneous={MAX_SIMULTANEOUS_DEVICES}: {devices}")
        run_workers(devices)
