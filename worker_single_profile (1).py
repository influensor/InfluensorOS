"""Independent InfluensorOS worker with cross-device target-profile locking.

This file intentionally reuses the existing InfluensorOS engine modules and does
not modify worker.py or any existing project file.

Concurrency note: the SQLite lock database coordinates workers running on the
same computer and sharing the same local state directory. If devices are split
across different computers, replace this local lock store with a shared database.
"""

import os
import random
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager

from engine.logger import info, warn, error

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

SUPPORTED_ACTIONS = {"like", "comment", "save", "share","repost", "interested"}


# ----------------------------
# Tunables
# ----------------------------
# Set MIN_POSTS_PER_ACCOUNT_PER_DEVICE / MAX_POSTS_PER_ACCOUNT_PER_DEVICE
# above to control each source account's random post quota for this device.
ACCOUNT_COOLDOWN = 3
CYCLE_COOLDOWN = 5
IDLE_RETRY_SECONDS = 5
MAX_ACCOUNT_SWITCHES_MIN = 5
MAX_ACCOUNT_SWITCHES_MAX = 10

# Per source-account usage budget, per device, for one running script process.
# Each source account gets a random post quota the first time it is encountered.
MIN_POSTS_PER_ACCOUNT_PER_DEVICE = 1
MAX_POSTS_PER_ACCOUNT_PER_DEVICE = 5

PROFILE_LOCK_LEASE_SECONDS = 600
PROFILE_LOCK_HEARTBEAT_SECONDS = 30

# In-memory by design: restarting this script starts a fresh account-usage cycle.
_ACCOUNT_POST_USAGE = {}
_ACCOUNT_POST_USAGE_LOCK = threading.Lock()


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


def _account_post_budget(device_id, account):
    """Return (completed_posts, random_limit), assigning a limit once per run."""
    account_key = _account_usage_key(account)
    if not account_key:
        return 0, MAX_POSTS_PER_ACCOUNT_PER_DEVICE

    device_key = str(device_id)
    with _ACCOUNT_POST_USAGE_LOCK:
        device_usage = _ACCOUNT_POST_USAGE.setdefault(device_key, {})
        record = device_usage.get(account_key)
        if record is None:
            low = max(1, int(MIN_POSTS_PER_ACCOUNT_PER_DEVICE))
            high = max(low, int(MAX_POSTS_PER_ACCOUNT_PER_DEVICE))
            record = {"posts": 0, "limit": random.randint(low, high)}
            device_usage[account_key] = record
            info(
                f"Account post budget assigned: account={account_key} "
                f"device={device_id} limit={record['limit']} posts",
                device_id,
            )
        return record["posts"], record["limit"]


def _account_budget_exhausted(device_id, account):
    posts, limit = _account_post_budget(device_id, account)
    return posts >= limit


def _record_account_post(device_id, account):
    """Count one handled post for this source account on this device."""
    account_key = _account_usage_key(account)
    if not account_key:
        return

    device_key = str(device_id)
    with _ACCOUNT_POST_USAGE_LOCK:
        device_usage = _ACCOUNT_POST_USAGE.setdefault(device_key, {})
        record = device_usage.get(account_key)
        if record is None:
            low = max(1, int(MIN_POSTS_PER_ACCOUNT_PER_DEVICE))
            high = max(low, int(MAX_POSTS_PER_ACCOUNT_PER_DEVICE))
            record = {"posts": 0, "limit": random.randint(low, high)}
            device_usage[account_key] = record
        record["posts"] += 1
        posts, limit = record["posts"], record["limit"]

    if posts >= limit:
        info(
            f"Account exhausted for this script run: account={account_key} "
            f"device={device_id} posts={posts}/{limit}; it will not be used again",
            device_id,
        )
    else:
        info(
            f"Account post budget: account={account_key} device={device_id} "
            f"posts={posts}/{limit}",
            device_id,
        )


# ----------------------------
# Shared target-profile lock
# ----------------------------
def _lock_database_path():
    """Keep the lock DB alongside the existing device-state directory."""
    from engine.config import STATE_DEVICES_DIR

    state_root = os.path.dirname(os.path.abspath(STATE_DEVICES_DIR))
    os.makedirs(state_root, exist_ok=True)
    return os.path.join(state_root, "influensor_profile_locks.sqlite3")


def _connect_lock_db():
    conn = sqlite3.connect(_lock_database_path(), timeout=30)
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute(
        """CREATE TABLE IF NOT EXISTS profile_locks (
            profile_key TEXT PRIMARY KEY,
            owner_token TEXT NOT NULL,
            device_id TEXT NOT NULL,
            lease_until REAL NOT NULL,
            updated_at REAL NOT NULL
        )"""
    )
    conn.commit()
    return conn


def _profile_key(customer):
    # Target/customer profile, not the rotating source Instagram account.
    username = str(customer.get("username") or "").strip().lstrip("@").lower()
    customer_id = str(customer.get("customer_id") or "").strip()
    return f"username:{username}" if username else f"customer_id:{customer_id}"


class ProfileLease:
    """A renewable lease preventing two local devices processing one profile."""

    def __init__(self, customer, device_id):
        self.profile_key = _profile_key(customer)
        self.device_id = str(device_id)
        self.owner_token = f"{self.device_id}:{os.getpid()}:{uuid.uuid4().hex}"
        self._stop = threading.Event()
        self._heartbeat_thread = None
        self.acquired = False

    def acquire(self):
        now = time.time()
        conn = _connect_lock_db()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT owner_token, lease_until FROM profile_locks WHERE profile_key=?",
                (self.profile_key,),
            ).fetchone()

            if row and row[0] != self.owner_token and row[1] > now:
                conn.rollback()
                return False

            conn.execute(
                """INSERT INTO profile_locks
                   (profile_key, owner_token, device_id, lease_until, updated_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(profile_key) DO UPDATE SET
                     owner_token=excluded.owner_token,
                     device_id=excluded.device_id,
                     lease_until=excluded.lease_until,
                     updated_at=excluded.updated_at""",
                (
                    self.profile_key,
                    self.owner_token,
                    self.device_id,
                    now + PROFILE_LOCK_LEASE_SECONDS,
                    now,
                ),
            )
            conn.commit()
            self.acquired = True
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            name=f"profile-lock-{self.device_id}",
            daemon=True,
        )
        self._heartbeat_thread.start()
        return True

    def _heartbeat_loop(self):
        while not self._stop.wait(PROFILE_LOCK_HEARTBEAT_SECONDS):
            conn = None
            try:
                conn = _connect_lock_db()
                now = time.time()
                cur = conn.execute(
                    """UPDATE profile_locks
                       SET lease_until=?, updated_at=?
                       WHERE profile_key=? AND owner_token=?""",
                    (
                        now + PROFILE_LOCK_LEASE_SECONDS,
                        now,
                        self.profile_key,
                        self.owner_token,
                    ),
                )
                conn.commit()
                if cur.rowcount != 1:
                    # Ownership was lost; stop renewing. Caller should not assume
                    # the lease is still valid after this point.
                    self._stop.set()
                    return
            except Exception as exc:
                # A transient DB error is logged; lease expiry is the fail-safe.
                warn(f"Profile-lock heartbeat failed: {exc}", self.device_id)
            finally:
                if conn is not None:
                    conn.close()

    def release(self):
        self._stop.set()
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=2)
        if not self.acquired:
            return
        conn = _connect_lock_db()
        try:
            conn.execute(
                "DELETE FROM profile_locks WHERE profile_key=? AND owner_token=?",
                (self.profile_key, self.owner_token),
            )
            conn.commit()
        finally:
            conn.close()
        self.acquired = False

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError("Target profile is already locked")
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()


@contextmanager
def _profile_lease(customer, device_id):
    lease = ProfileLease(customer, device_id)
    if not lease.acquire():
        yield None
        return
    try:
        yield lease
    finally:
        lease.release()


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
    """Pick/resume one customer without ever processing a locked profile."""
    eligible_ids = [c["customer_id"] for c in customers]

    # Resume an in-progress customer first. Do not overwrite its checkpoint if
    # another device currently owns that target profile's lock.
    if checkpoint.get("customer_id"):
        resumed = _customer_by_id(customers, checkpoint["customer_id"])
        if resumed:
            lease = ProfileLease(resumed, device_id)
            if lease.acquire():
                return resumed, lease, True
            info(
                f"Resume waits: @{resumed.get('username')} is locked by another device",
                device_id,
            )
            return None, None, False

        clear_checkpoint(device_id)
        checkpoint = {}

    if not eligible_ids:
        return None, None, False

    first_id = get_next_customer(device_id, eligible_ids)
    cycle = load_cycle(device_id) or {}
    order = list(cycle.get("cycle_order") or [])

    # Prefer the cycle manager's shuffled order; rotate from its next candidate.
    if first_id in order:
        start = order.index(first_id)
        ordered_ids = order[start:] + order[:start]
    else:
        ordered_ids = [first_id] + [cid for cid in eligible_ids if cid != first_id]

    # Ignore removed/ineligible ids and try every candidate once.
    valid_ids = set(str(cid) for cid in eligible_ids)
    seen = set()
    for customer_id in ordered_ids:
        if str(customer_id) not in valid_ids or str(customer_id) in seen:
            continue
        seen.add(str(customer_id))
        customer = _customer_by_id(customers, customer_id)
        if not customer:
            continue

        lease = ProfileLease(customer, device_id)
        if lease.acquire():
            return customer, lease, False

    return None, None, False


def _load_customer_post(device_id, customer, checkpoint, resumed):
    # Match worker.py: once a post is selected, keep using that exact post for
    # the entire account-switch pass, even if delivery tracking reaches completed
    # before the switch limit. Delivery status must not change the active post
    # mid-pass. The checkpoint is cleared only after the account-switch loop ends.
    if resumed:
        post = checkpoint.get("post")
        if (
            isinstance(post, dict)
            and post.get("url")
            and post.get("shortcode")
        ):
            info(
                f"Resuming same post {post['shortcode']} for @{customer.get('username')} "
                "(delivery status does not change the active post during this pass)",
                device_id,
            )
            return post

    posts = load_posts(customer, device_id)
    if not posts:
        return None
    post = posts[0]
    return post if isinstance(post, dict) else None


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

    while switches_this_post < max_account_switches:
        # An account restored from a checkpoint is processed before switching.
        if not active_account:
            next_account = switch_account(device_id)
            if not next_account:
                warn("Account switcher returned no account; ending this customer pass", device_id)
                break
            active_account = next_account
            switches_this_post += 1
            _save_worker_checkpoint(
                device_id, customer, post, account_index, active_account
            )
            # Give Instagram time to finish switching accounts before navigation.
            time.sleep(ACCOUNT_COOLDOWN)

        # Once this account has handled its randomly assigned number of posts
        # on this device, never run it again until this script process restarts.
        if _account_budget_exhausted(device_id, active_account):
            account_key = _account_usage_key(active_account)
            posts_used, post_limit = _account_post_budget(device_id, active_account)
            info(
                f"Skipping exhausted source account={account_key} on device={device_id} "
                f"({posts_used}/{post_limit} posts this run)",
                device_id,
            )
            active_account = None
            account_index += 1
            _save_worker_checkpoint(
                device_id, customer, post, account_index, active_account
            )
            continue

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
                # One post handled for this source account on this device.
                # Its in-memory quota persists across later customer/post loops.
                _record_account_post(device_id, active_account)
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
            raise
        finally:
            # Account switching happens only after the current account's work
            # and delivery-tracking decision have finished.
            pass

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
        # Only advance to another post after this exact post has reached its
        # expected account-delivery count.
        mark_customer_completed(device_id, customer["customer_id"])
        clear_checkpoint(device_id)
        info(
            f"Post completed; next loop may select another post: "
            f"{customer['customer_id']} / {post.get('shortcode')}",
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
            warn("No eligible customers; retrying", device_id)
            time.sleep(IDLE_RETRY_SECONDS)
            continue

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
                    f"No incomplete posts for @{customer.get('username')}; marking customer visited",
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
    """Start one worker thread per connected/authorized device."""
    threads = []
    for device_id in device_ids:
        thread = threading.Thread(
            target=device_worker,
            args=(device_id, max_cycles_per_device),
            name=f"influensor-worker-{device_id}",
            daemon=True,
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    from engine.logic.device_auth import get_authorized_devices

    devices = get_authorized_devices()
    if not devices:
        print("No authorized ADB devices connected.")
    else:
        print(f"Starting independent worker on {len(devices)} device(s): {devices}")
        run_workers(devices)
