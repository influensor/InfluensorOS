import os
import re
import time
import random

from engine.ui.device import get_device
from engine.logger import info, warn, error


# =========================
# CONFIG
# =========================

MENTIONS_FILE = os.path.join("data","mentions","usernames.txt")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._]{1,30}$")

# =========================
# SELECTORS (same approach as comment.py)
# =========================

COMMENT_BUTTON_SELECTORS = [
    {"descriptionContains": "Comment"},
    {"text": "Comment"},
    {"resourceId": "com.instagram.android:id/row_feed_button_comment"},
]

COMMENT_INPUT_SELECTORS = [
    {"resourceId": "com.instagram.android:id/layout_comment_thread_edittext_multiline"},
    {"resourceId": "com.instagram.android:id/comment_edit_text"},
    {"resourceId": "com.instagram.android:id/layout_comment_thread_edittext"},
    {"resourceId": "com.instagram.android:id/row_comment_textview"},
    {"className": "android.widget.EditText"},
    {"className": "android.widget.AutoCompleteTextView"},
    {"textContains": "Add a comment"},
    {"textContains": "Join the conversation"},
    {"textContains": "What do you think of this?"},
]

SEND_BUTTON_SELECTORS = [
    {"resourceId": "com.instagram.android:id/layout_comment_thread_post_button_icon"},
    {"descriptionContains": "Post"},
    {"descriptionContains": "Send"},
    {"text": "Post"},
    {"text": "Send"},
]

# Coordinates from comment_delete_menu.xml (1080x2400 screenshot hierarchy).
COMMENT_X = 600
COMMENT_Y = 990

DELETE_SELECTOR = "com.instagram.android:id/context_menu_item"


def find_delete_item(d):
    """Return the Delete menu item if Instagram exposes it."""
    item = d(
        resourceId=DELETE_SELECTOR,
        description="Delete",
    )
    if item.exists:
        return item

    # Fallback for Instagram versions where the description is exposed
    # but the resource-id differs.
    item = d(description="Delete")
    if item.exists:
        return item

    item = d(text="Delete")
    if item.exists:
        return item

    return None


def delete_posted_comment(d, device_id):
    """Long-press the posted comment and delete it from Instagram's menu."""
    print(f"Long-pressing comment row at ({COMMENT_X}, {COMMENT_Y})...")
    d.long_click(COMMENT_X, COMMENT_Y, duration=1.2)
    time.sleep(1.5)

    delete_item = find_delete_item(d)
    if delete_item is None:
        warn("Delete option was not detected; comment was not deleted", device_id)
        return False

    info("Delete option detected; tapping Delete", device_id)
    delete_item.click()

    # This Instagram version deletes the comment immediately; no second
    # confirmation dialog is displayed.
    time.sleep(2)
    info("🗑 Delete option tapped; Instagram deletion action completed", device_id)
    return True

# =========================
# TXT LOADER
# =========================

def load_usernames(path=MENTIONS_FILE):
    """Load unique, valid usernames. Accepts lines with or without @."""
    if not os.path.isfile(path):
        warn(f"Mention file not found: {path}")
        return []

    usernames = []
    seen = set()

    try:
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                username = line.strip().lstrip("@").strip()

                if not username or username.startswith("#"):
                    continue

                if not USERNAME_PATTERN.fullmatch(username):
                    warn(f"Skipping invalid username: {line.strip()}")
                    continue

                key = username.casefold()
                if key not in seen:
                    seen.add(key)
                    usernames.append(username)

    except Exception as e:
        error(f"Failed loading mention usernames: {e}")
        return []

    return usernames


def remove_username(username, path=MENTIONS_FILE):
    """
    Remove a username from the TXT file after its mention action succeeds.
    Matching is case-insensitive and accepts entries with or without @.
    """
    username = _normalize_username(username)

    if not username:
        return False

    if not os.path.isfile(path):
        warn(f"Mention file not found: {path}")
        return False

    try:
        with open(path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        kept_lines = []
        removed = False

        for line in lines:
            value = line.strip().lstrip("@").strip()

            if value and value.casefold() == username.casefold():
                removed = True
                continue

            kept_lines.append(line)

        if removed:
            temp_path = path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as file:
                file.writelines(kept_lines)
            os.replace(temp_path, path)

        return removed

    except Exception as e:
        error(f"Failed removing @{username} from mention file: {e}")
        return False


# =========================
# HELPERS
# =========================

def _find_ui(d, selectors, timeout=2):
    for selector in selectors:
        ui = d(**selector)
        if ui.exists(timeout=timeout):
            return ui
    return None


def _normalize_username(username):
    if not isinstance(username, str):
        return None

    value = username.strip().lstrip("@").strip()

    if not USERNAME_PATTERN.fullmatch(value):
        return None

    return value


# =========================
# MENTION ACTION
# =========================

def post_mention(device_id, username, retries=2):
    """
    Post one @username comment.

    Posts one @username comment, deletes that posted comment, and then
    removes the username from the source TXT file. It does not run a
    bulk posting loop.
    """
    username = _normalize_username(username)

    if not username:
        warn("Invalid mention username", device_id)
        return False

    mention_text = f"@{username}"
    d = get_device(device_id)

    for attempt in range(1, retries + 1):
        info(f"▶ Mention Post (attempt {attempt}): {mention_text}", device_id)

        try:
            # 1. Open comments only if the input is not already visible.
            input_box = _find_ui(d, COMMENT_INPUT_SELECTORS, timeout=1)

            if not input_box:
                comment_btn = _find_ui(d, COMMENT_BUTTON_SELECTORS)

                if not comment_btn:
                    warn("Comment button not found", device_id)
                    time.sleep(1)
                    continue

                comment_btn.click()
                time.sleep(random.uniform(2, 3))

            # 2. Locate comment input.
            input_box = _find_ui(d, COMMENT_INPUT_SELECTORS)

            if not input_box:
                warn("Comment input not found", device_id)
                continue

            # 3. Focus input.
            try:
                input_box.click()
            except Exception as e:
                warn(f"Failed to focus comment input: {e}", device_id)
                continue

            time.sleep(random.uniform(0.5, 1.0))

            # 4. Enter the mention.
            try:
                d.clear_text()
            except Exception:
                pass

            try:
                d.send_keys(mention_text, clear=False)
                time.sleep(1)
            except Exception as e:
                warn(f"Failed to enter mention: {e}", device_id)
                continue

            # 5. Hide keyboard so the Post button can be located.
            try:
                d.press("back")
                time.sleep(0.8)
            except Exception:
                pass

            send_btn = _find_ui(d, SEND_BUTTON_SELECTORS, timeout=2)

            if not send_btn:
                warn("Post button not found; mention was not submitted", device_id)
                continue

            send_btn.click()
            time.sleep(random.uniform(1.5, 2.5))

            info(
                f"✅ Mention comment submitted: {mention_text}",
                device_id
            )

            # Give Instagram time to render the newly posted comment.
            time.sleep(random.uniform(1, 5))

            # Delete the comment before removing the username from the TXT file.
            if not delete_posted_comment(d, device_id):
                error(
                    f"Could not delete posted mention comment: {mention_text}",
                    device_id
                )
                return False

            # Remove from the source list only after deletion succeeds.
            if remove_username(username):
                info(f"🗑 Removed @{username} from {MENTIONS_FILE}", device_id)
            else:
                warn(
                    f"Could not remove @{username} from {MENTIONS_FILE}; "
                    "it may be missing or the file could not be updated.",
                    device_id
                )

            return True

        except Exception as e:
            error(f"Mention attempt crashed: {e}", device_id)
            time.sleep(1)

    error(f"❌ Mention failed after {retries} attempts: {mention_text}", device_id)
    return False
