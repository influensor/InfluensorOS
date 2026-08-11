import os
import time
import random

from engine.ui.device import get_device
from engine.logger import info, warn, error
from engine.ui.swipe import swipe_up
from engine.config import STATE_DEVICES_DIR


# =========================================================
# CONFIG
# =========================================================

CUSTOM_SHARE_FILE = "share_custom_users.txt"


# =========================================================
# SELECTOR CANDIDATES
# =========================================================

SHARE_BUTTON_SELECTORS = [
    {"resourceId": "com.instagram.android:id/row_feed_button_share"},
    {"descriptionContains": "Share"},
    {"text": "Share"},
]


SEARCH_SELECTORS = [
    {"resourceId": "com.instagram.android:id/direct_share_search"},
    {"resourceId": "com.instagram.android:id/search_edit_text"},
    {"resourceId": "com.instagram.android:id/direct_share_sheet_search"},
    {"text": "Search"},
    {"descriptionContains": "Search"},
]


USER_ROW_SELECTORS = [
    {
        "resourceId":
        "com.instagram.android:id/row_user_info_layout"
    },
]


USER_NAME_SELECTORS = [
    {
        "resourceId":
        "com.instagram.android:id/row_user_primary_name"
    },
]


SEND_BUTTON_SELECTORS = [
    {
        "resourceId":
        "com.instagram.android:id/direct_send_button_multi_select"
    },
    {
        "text": "Send separately"
    },
    {
        "text": "Send"
    },
]


# =========================================================
# UNIVERSAL FIND FUNCTION
# =========================================================

def _find_ui(
    d,
    selectors,
    timeout=0.1,
    multiple=False
):

    for sel in selectors:

        try:

            ui = d(**sel)

            if multiple:

                if len(ui) > 0:
                    return list(ui)

            else:

                if ui.exists(
                    timeout=timeout
                ):
                    return ui

        except Exception:

            continue

    return [] if multiple else None


# =========================================================
# CUSTOM SHARE FILE
# =========================================================

def _get_custom_share_file(
    device_id
):

    return os.path.join(
        STATE_DEVICES_DIR,
        device_id,
        CUSTOM_SHARE_FILE
    )


# =========================================================
# LOAD CUSTOM USERS
# =========================================================

def _load_custom_users(
    device_id
):

    path = _get_custom_share_file(
        device_id
    )

    if not os.path.exists(path):

        warn(
            f"⚠ Custom Share File Not Found: {path}",
            device_id
        )

        return []

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            users = []

            for line in f:

                username = line.strip()

                if not username:
                    continue

                username = (
                    username
                    .lstrip("@")
                    .strip()
                )

                if username:

                    users.append(
                        username
                    )

            return users

    except Exception as e:

        warn(
            f"Custom Share File Read Error: {e}",
            device_id
        )

        return []


# =========================================================
# GET FIRST CUSTOM USER
# =========================================================

def _get_custom_user(
    device_id
):

    users = _load_custom_users(
        device_id
    )

    if not users:

        info(
            "No Custom Share Users Available",
            device_id
        )

        return None

    username = users[0]

    info(
        f"▶ Custom Share Target: @{username}",
        device_id
    )

    return username


# =========================================================
# REMOVE CUSTOM USER
# =========================================================

def _remove_custom_user(
    device_id,
    username
):

    path = _get_custom_share_file(
        device_id
    )

    users = _load_custom_users(
        device_id
    )

    if not users:

        return False

    updated = []
    removed = False

    for user in users:

        if (
            not removed
            and user.lower() == username.lower()
        ):

            removed = True
            continue

        updated.append(
            user
        )

    if not removed:

        return False

    try:

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            for user in updated:

                f.write(
                    user + "\n"
                )

        info(
            f"✓ Removed @{username} "
            f"from custom share queue",
            device_id
        )

        return True

    except Exception as e:

        warn(
            f"Custom Share File Update Error: {e}",
            device_id
        )

        return False


# =========================================================
# OPEN SHARE SHEET
# =========================================================

def _open_share_sheet(
    d,
    device_id
):

    share_btn = _find_ui(
        d,
        SHARE_BUTTON_SELECTORS,
        timeout=2
    )

    if not share_btn:

        warn(
            "⚠ Share Button Not Found",
            device_id
        )

        return False

    try:

        share_btn.click()

        time.sleep(
            random.uniform(
                0.1,
                0.5
            )
        )

        return True

    except Exception as e:

        warn(
            f"Share Click Error: {e}",
            device_id
        )

        return False


# =========================================================
# EXPAND SHARE SHEET
# =========================================================

def _expand_share_sheet(
    device_id
):

    try:

        swipe_up(
            device_id
        )

        return True

    except Exception as e:

        warn(
            f"Share Sheet Expand Error: {e}",
            device_id
        )

        return False


# =========================================================
# SEARCH USER
# =========================================================

def _search_user(
    d,
    device_id,
    username
):

    search = _find_ui(
        d,
        SEARCH_SELECTORS,
        timeout=2
    )

    if not search:

        warn(
            "⚠ Share Search Box Not Found",
            device_id
        )

        return False

    try:

        search.click()

        time.sleep(
            random.uniform(
                0.2,
                0.4
            )
        )

        # -------------------------------------------------
        # Clear previous text
        # -------------------------------------------------

        try:

            search.clear_text()

        except Exception:

            pass

        # -------------------------------------------------
        # Enter username
        # -------------------------------------------------

        search.set_text(
            username
        )

        # -------------------------------------------------
        # Wait for Instagram results
        # -------------------------------------------------

        time.sleep(
            random.uniform(
                2.0,
                3.0
            )
        )

        info(
            f"Searching Custom User: @{username}",
            device_id
        )

        return True

    except Exception as e:

        warn(
            f"Username Search Error: {e}",
            device_id
        )

        return False


# =========================================================
# GET USERNAME FROM USER ROW
# =========================================================

def _get_row_username(
    row
):

    try:

        name = row.child(
            resourceId=
            "com.instagram.android:id/row_user_primary_name"
        )

        if name.exists:

            try:

                username = (
                    name.get_text()
                    or ""
                ).strip()

                if username:

                    return username

            except Exception:

                pass

            try:

                username = (
                    name.info.get(
                        "text",
                        ""
                    )
                    or ""
                ).strip()

                if username:

                    return username

            except Exception:

                pass

    except Exception:

        pass

    return ""


# =========================================================
# FIND EXACT USER
# =========================================================

def _find_exact_user(
    d,
    username,
    device_id
):

    target = (
        username
        .lstrip("@")
        .strip()
        .lower()
    )

    try:

        rows = _find_ui(
            d,
            USER_ROW_SELECTORS,
            multiple=True
        )

        if not rows:

            return None

        # -------------------------------------------------
        # Check Instagram rows in displayed order
        # -------------------------------------------------

        for row in rows:

            try:

                row_username = (
                    _get_row_username(
                        row
                    )
                )

                if not row_username:

                    continue

                clean_username = (
                    row_username
                    .lstrip("@")
                    .strip()
                    .lower()
                )

                if clean_username == target:

                    info(
                        f"✓ Exact User Found: "
                        f"@{username}",
                        device_id
                    )

                    return row

            except Exception:

                continue

    except Exception as e:

        warn(
            f"Exact User Match Error: {e}",
            device_id
        )

    return None


# =========================================================
# FIND FIRST AVAILABLE USER
# =========================================================

def _find_first_user(
    d,
    device_id
):

    try:

        users = _find_ui(
            d,
            USER_ROW_SELECTORS,
            multiple=True
        )

        if not users:

            warn(
                "⚠ Share Sheet Returned No Users",
                device_id
            )

            return None

        # -------------------------------------------------
        # IMPORTANT:
        #
        # The first row is the first available
        # actual Share user.
        # -------------------------------------------------

        user = users[0]

        username = _get_row_username(
            user
        )

        if username:

            info(
                f"First Available Share User: "
                f"{username}",
                device_id
            )

        else:

            info(
                "First Available Share User Found",
                device_id
            )

        return user

    except Exception as e:

        warn(
            f"First Available User Error: {e}",
            device_id
        )

        return None


# =========================================================
# SELECT USER
# =========================================================

def _select_user(
    d,
    device_id,
    username
):

    # =====================================================
    # TRY EXACT USER FIRST
    # =====================================================

    try:

        user = _find_exact_user(
            d,
            username,
            device_id
        )

    except Exception as e:

        warn(
            f"Exact User Selection Exception: {e}",
            device_id
        )

        user = None

    # =====================================================
    # FALLBACK TO FIRST USER
    # =====================================================

    if not user:

        info(
            f"Exact User Not Found → "
            f"Checking First Available User",
            device_id
        )

        user = _find_first_user(
            d,
            device_id
        )

        # -------------------------------------------------
        # NO USERS AVAILABLE
        # -------------------------------------------------

        if not user:

            warn(
                "⚠ No Users Available In Share Sheet",
                device_id
            )

            return "NO_USERS"

    # =====================================================
    # CLICK USER ROW
    # =====================================================

    try:

        user.click()

        time.sleep(
            random.uniform(
                0.2,
                0.5
            )
        )

        info(
            "✓ Share User Selected",
            device_id
        )

        return "SELECTED"

    except Exception as e:

        warn(
            f"User Click Error: {e}",
            device_id
        )

        return "ERROR"


# =========================================================
# CLICK SEND
# =========================================================

def _click_send(
    d,
    device_id
):

    send_btn = _find_ui(
        d,
        SEND_BUTTON_SELECTORS,
        timeout=3
    )

    if not send_btn:

        warn(
            "⚠ Send Button Not Found",
            device_id
        )

        return False

    try:

        send_btn.click()

        info(
            "🚀 Custom Share Sent Successfully",
            device_id
        )

        time.sleep(
            1
        )

        return True

    except Exception as e:

        warn(
            f"Send Click Error: {e}",
            device_id
        )

        return False


# =========================================================
# HANDLE RETRY
# =========================================================

def _handle_retry(
    device_id
):

    warn(
        "Retrying Custom Share...",
        device_id
    )

    time.sleep(
        1
    )


# =========================================================
# MAIN CUSTOM SHARE
# =========================================================

def share_custom(
    device_id,
    retries=2
):

    """
    CUSTOM SHARE FLOW

    1. Get first username from TXT.
    2. Open Share.
    3. Expand Share sheet.
    4. Search username.
    5. Try exact username.
    6. If exact username unavailable:
         select first available user.
    7. If NO users are available:
         remove username from TXT.
    8. If user is selected:
         click Send.
    9. If Send succeeds:
         remove username from TXT.
    10. If UI/Send fails:
         keep username for retry.
    """

    d = get_device(
        device_id
    )

    # =====================================================
    # GET FIRST QUEUED USER
    # =====================================================

    username = _get_custom_user(
        device_id
    )

    if not username:

        return False

    # =====================================================
    # RETRIES
    # =====================================================

    for attempt in range(
        1,
        retries + 1
    ):

        info(
            f"▶ Custom Share "
            f"(attempt {attempt}/{retries}) "
            f"→ @{username}",
            device_id
        )

        # =================================================
        # OPEN SHARE
        # =================================================

        if not _open_share_sheet(
            d,
            device_id
        ):

            continue

        # =================================================
        # EXPAND
        # =================================================

        _expand_share_sheet(
            device_id
        )

        # =================================================
        # SEARCH
        # =================================================

        if not _search_user(
            d,
            device_id,
            username
        ):

            _handle_retry(
                device_id
            )

            continue

        # =================================================
        # SELECT USER
        # =================================================

        selection = _select_user(
            d,
            device_id,
            username
        )

        # =================================================
        # NO USERS AVAILABLE
        # =================================================

        if selection == "NO_USERS":

            info(
                f"Removing @{username} "
                f"because Share returned no users",
                device_id
            )

            removed = _remove_custom_user(
                device_id,
                username
            )

            if removed:

                info(
                    f"✓ @{username} removed "
                    f"from custom share queue",
                    device_id
                )

            else:

                warn(
                    f"⚠ Could not remove @{username} "
                    f"from custom share queue",
                    device_id
                )

            return False

        # =================================================
        # SELECTION ERROR
        # =================================================

        if selection == "ERROR":

            _handle_retry(
                device_id
            )

            continue

        # =================================================
        # UNKNOWN RESULT
        # =================================================

        if selection != "SELECTED":

            _handle_retry(
                device_id
            )

            continue

        # =================================================
        # SEND
        # =================================================

        if _click_send(
            d,
            device_id
        ):

            # ---------------------------------------------
            # Remove ONLY after successful Send
            # ---------------------------------------------

            removed = _remove_custom_user(
                device_id,
                username
            )

            if removed:

                info(
                    f"✓ @{username} completed "
                    f"and removed from queue",
                    device_id
                )

            else:

                warn(
                    f"⚠ Share succeeded but "
                    f"could not remove @{username} "
                    f"from queue",
                    device_id
                )

            return True

        # =================================================
        # SEND FAILED
        # =================================================

        _handle_retry(
            device_id
        )

    # =====================================================
    # FINAL FAILURE
    # =====================================================

    error(
        f"❌ Custom Share Failed After Retries "
        f"→ @{username}",
        device_id
    )

    # IMPORTANT:
    # Username remains in TXT because the operation
    # did not reach successful Send.

    return False
