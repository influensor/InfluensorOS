import os
import time
import random

from engine.ui.device import get_device
from engine.logger import info, warn, error
from engine.ui.swipe import swipe_up


# =========================================================
# CONFIG
# =========================================================

CUSTOM_SHARE_FILENAME = "share_custom_users.txt"


# =========================================================
# SELECTORS
# =========================================================

SHARE_BUTTON_SELECTORS = [
    {
        "resourceId":
        "com.instagram.android:id/row_feed_button_share"
    },
    {
        "descriptionContains": "Share"
    },
    {
        "text": "Share"
    },
]


# ---------------------------------------------------------
# Share sheet search selectors
# ---------------------------------------------------------

SEARCH_SELECTORS = [
    {
        "resourceId":
        "com.instagram.android:id/direct_share_search"
    },
    {
        "resourceId":
        "com.instagram.android:id/search_edit_text"
    },
    {
        "resourceId":
        "com.instagram.android:id/direct_share_sheet_search"
    },
    {
        "text": "Search"
    },
    {
        "descriptionContains": "Search"
    },
]


# ---------------------------------------------------------
# Send button
# ---------------------------------------------------------

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
# CUSTOM SHARE FILE
# =========================================================

def _get_users_file(device_id):

    """
    Returns:

    runtime/state/devices/<device_id>/custom_share_users.txt
    """

    return os.path.join(
        "runtime",
        "state",
        "devices",
        device_id,
        CUSTOM_SHARE_FILENAME
    )


# =========================================================
# LOAD USERS
# =========================================================

def _load_users(device_id):

    path = _get_users_file(
        device_id
    )

    if not os.path.exists(path):

        warn(
            f"Custom share file not found: {path}",
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

                # Remove @ if present
                username = username.lstrip("@").strip()

                if not username:
                    continue

                users.append(username)

        return users

    except Exception as e:

        error(
            f"Failed loading custom share users: {e}",
            device_id
        )

        return []


# =========================================================
# SAVE USERS
# =========================================================

def _save_users(
    device_id,
    users
):

    path = _get_users_file(
        device_id
    )

    try:

        folder = os.path.dirname(
            path
        )

        os.makedirs(
            folder,
            exist_ok=True
        )

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            for username in users:

                f.write(
                    username + "\n"
                )

        return True

    except Exception as e:

        error(
            f"Failed saving custom share users: {e}",
            device_id
        )

        return False


# =========================================================
# GET ONE USER
# =========================================================

def _get_next_user(device_id):

    users = _load_users(
        device_id
    )

    if not users:

        info(
            "No custom share users available",
            device_id
        )

        return None

    # -----------------------------------------------------
    # Take ONLY first user
    # -----------------------------------------------------

    username = users[0]

    info(
        f"Custom share target: @{username}",
        device_id
    )

    return username


# =========================================================
# REMOVE SUCCESSFUL USER
# =========================================================

def _remove_user(
    device_id,
    username
):

    users = _load_users(
        device_id
    )

    if not users:
        return False

    updated_users = []

    removed = False

    for user in users:

        if (
            not removed
            and user.lower() == username.lower()
        ):

            removed = True
            continue

        updated_users.append(
            user
        )

    if not removed:

        return False

    return _save_users(
        device_id,
        updated_users
    )


# =========================================================
# UNIVERSAL FIND
# =========================================================

def _find_ui(
    d,
    selectors,
    timeout=0.1,
    multiple=False
):

    for selector in selectors:

        try:

            ui = d(
                **selector
            )

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

    if multiple:

        return []

    return None


# =========================================================
# OPEN SHARE SHEET
# =========================================================

def _open_share_sheet(
    d,
    device_id
):

    share_button = _find_ui(
        d,
        SHARE_BUTTON_SELECTORS,
        timeout=2
    )

    if not share_button:

        warn(
            "Custom Share: Share button not found",
            device_id
        )

        return False

    try:

        share_button.click()

        time.sleep(
            random.uniform(
                0.3,
                0.7
            )
        )

        info(
            "Custom Share: Share sheet opened",
            device_id
        )

        return True

    except Exception as e:

        warn(
            f"Custom Share: Share click error: {e}",
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

        time.sleep(
            random.uniform(
                0.2,
                0.5
            )
        )

        return True

    except Exception as e:

        warn(
            f"Custom Share: Expand failed: {e}",
            device_id
        )

        return False


# =========================================================
# FIND SEARCH BOX
# =========================================================

def _find_search_box(
    d,
    device_id
):

    search = _find_ui(
        d,
        SEARCH_SELECTORS,
        timeout=2
    )

    if search:

        return search

    return None


# =========================================================
# SEARCH USERNAME
# =========================================================

def _search_username(
    d,
    device_id,
    username
):

    search = _find_search_box(
        d,
        device_id
    )

    if not search:

        warn(
            "Custom Share: Search box not found",
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
        # Clear existing text
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

        time.sleep(
            random.uniform(
                1.0,
                2.0
            )
        )

        info(
            f"Custom Share: Searching @{username}",
            device_id
        )

        return True

    except Exception as e:

        warn(
            f"Custom Share: Username search failed: {e}",
            device_id
        )

        return False


# =========================================================
# FIND USER RESULT
# =========================================================

def _find_user_result(
    d,
    username,
    device_id
):

    clean_username = (
        username
        .lstrip("@")
        .strip()
    )

    # -----------------------------------------------------
    # Exact text
    # -----------------------------------------------------

    exact_selectors = [

        {
            "text": clean_username
        },

        {
            "text": f"@{clean_username}"
        },

    ]

    for selector in exact_selectors:

        try:

            result = d(
                **selector
            )

            if result.exists(
                timeout=1
            ):

                return result

        except Exception:

            pass

    # -----------------------------------------------------
    # XPath exact text / content description
    # -----------------------------------------------------

    try:

        result = d.xpath(
            f"//*[@text='{clean_username}' "
            f"or @content-desc='{clean_username}']"
        )

        if result.exists:

            return result

    except Exception:

        pass

    # -----------------------------------------------------
    # Case-insensitive fallback
    #
    # uiautomator2 XPath does not provide a universal
    # case-insensitive contains, so inspect visible nodes.
    # -----------------------------------------------------

    try:

        nodes = d.xpath(
            "//*[@text or @content-desc]"
        )

        for node in nodes.all():

            try:

                text = (
                    node.attrib.get(
                        "text",
                        ""
                    )
                    or ""
                )

                content_desc = (
                    node.attrib.get(
                        "content-desc",
                        ""
                    )
                    or ""
                )

                text = text.strip().lstrip("@").lower()
                content_desc = (
                    content_desc
                    .strip()
                    .lstrip("@")
                    .lower()
                )

                target = (
                    clean_username
                    .lower()
                )

                if (
                    text == target
                    or content_desc == target
                ):

                    return node

            except Exception:

                continue

    except Exception:

        pass

    return None


# =========================================================
# SELECT USER
# =========================================================

def _select_user(
    d,
    device_id,
    username
):

    user = _find_user_result(
        d,
        username,
        device_id
    )

    if not user:

        warn(
            f"Custom Share: @{username} not found",
            device_id
        )

        return False

    try:

        user.click()

        time.sleep(
            random.uniform(
                0.3,
                0.6
            )
        )

        info(
            f"Custom Share: Selected @{username}",
            device_id
        )

        return True

    except Exception as e:

        warn(
            f"Custom Share: User selection failed: {e}",
            device_id
        )

        return False


# =========================================================
# CLICK SEND
# =========================================================

def _click_send(
    d,
    device_id
):

    send_button = _find_ui(
        d,
        SEND_BUTTON_SELECTORS,
        timeout=3
    )

    if not send_button:

        warn(
            "Custom Share: Send button not found",
            device_id
        )

        return False

    try:

        send_button.click()

        time.sleep(
            random.uniform(
                0.8,
                1.5
            )
        )

        info(
            "Custom Share: Sent successfully",
            device_id
        )

        return True

    except Exception as e:

        warn(
            f"Custom Share: Send click error: {e}",
            device_id
        )

        return False


# =========================================================
# MAIN CUSTOM SHARE
# =========================================================

def custom_share(
    device_id,
    retries=2
):

    """
    Custom Share Flow:

        1. Read first username from device TXT
        2. Open Share
        3. Expand Share sheet
        4. Search username
        5. Select ONE username
        6. Send
        7. Remove username only after success

    Returns:

        True  -> Share successful
        False -> Share failed / no username
    """

    # -----------------------------------------------------
    # Device
    # -----------------------------------------------------

    d = get_device(
        device_id
    )

    # -----------------------------------------------------
    # Get ONE username
    # -----------------------------------------------------

    username = _get_next_user(
        device_id
    )

    if not username:

        return False

    # -----------------------------------------------------
    # Retry
    # -----------------------------------------------------

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

            time.sleep(
                0.5
            )

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

        if not _search_username(
            d,
            device_id,
            username
        ):

            time.sleep(
                0.5
            )

            continue

        # =================================================
        # SELECT EXACTLY ONE
        # =================================================

        if not _select_user(
            d,
            device_id,
            username
        ):

            time.sleep(
                0.5
            )

            continue

        # =================================================
        # SEND
        # =================================================

        if _click_send(
            d,
            device_id
        ):

            # -------------------------------------------------
            # IMPORTANT:
            # Remove user ONLY after successful Send.
            # -------------------------------------------------

            removed = _remove_user(
                device_id,
                username
            )

            if removed:

                info(
                    f"Custom Share completed → "
                    f"@{username} "
                    f"(removed from queue)",
                    device_id
                )

            else:

                warn(
                    f"Custom Share sent to @{username}, "
                    f"but could not remove user from file",
                    device_id
                )

            return True

        # =================================================
        # SEND FAILED
        # =================================================

        time.sleep(
            random.uniform(
                0.5,
                1.0
            )
        )

    # =====================================================
    # FINAL FAILURE
    # =====================================================

    error(
        f"❌ Custom Share failed → @{username}",
        device_id
    )

    # User remains in TXT because the share
    # was not confirmed successful.

    return False
