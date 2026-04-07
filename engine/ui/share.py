import time
import random
from engine.ui.device import get_device
from engine.logger import info, warn, error
from engine.ui.swipe import swipe_up

# =========================
# SELECTOR CANDIDATES
# =========================

SHARE_BUTTON_SELECTORS = [
    {"resourceId": "com.instagram.android:id/row_feed_button_share"},
    {"descriptionContains": "Share"},
    {"text": "Share"},
]

USER_SELECTORS = [
    {"resourceId": "com.instagram.android:id/direct_share_sheet_grid_view_pog"},
]

SEND_BUTTON_SELECTORS = [
    {"resourceId": "com.instagram.android:id/direct_send_button_multi_select"},
    {"text": "Send separately"},
    {"text": "Send"},
]

# =========================
# UNIVERSAL FIND FUNCTION
# =========================

def _find_ui(d, selectors, timeout=0.1, multiple=False):
    for sel in selectors:
        ui = d(**sel)
        try:
            if multiple:
                if len(ui) > 0:
                    return list(ui)
            else:
                if ui.exists(timeout=timeout):
                    return ui
        except Exception:
            continue
    return [] if multiple else None

# =========================
# Open Share Sheet
# =========================

def _open_share_sheet(d, device_id):
    share_btn = _find_ui(d, SHARE_BUTTON_SELECTORS, timeout=2)
    if not share_btn:
        warn("⚠ Share Button Not Found", device_id)
        return False
    try:
        share_btn.click()
        time.sleep(random.uniform(0.1, 0.5))
        return True
    except Exception as e:
        warn(f"Share Click Error: {e}", device_id)
        return False

# =========================
# Expand Share Sheet
# =========================

def _expand_share_sheet(device_id):
    try:
        swipe_up(device_id)
        return True
    except Exception:
        return False

# =========================
# SELECT RANDOM USERS
# =========================

def _select_random_users(d, device_id):
    users = _find_ui(d, USER_SELECTORS, multiple=True)[:12]
    if not users:
        warn("⚠ No Users Found in Share Sheet", device_id)
        return 0
    random.shuffle(users)
    target = random.randint(1, min(5, len(users)))
    selected = 0
    for u in users:
        if selected >= target:
            break
        try:
            u.click()
            selected += 1
        except Exception:
            pass
    return selected

# =========================
# CLICK SEND
# =========================

def _click_send(d, device_id):
    send_btn = _find_ui(d, SEND_BUTTON_SELECTORS, timeout=3)
    if send_btn:
        try:
            send_btn.click()
            info("🚀 Shared Successfully", device_id)
            time.sleep(1)
            return True
        except Exception as e:
            warn(f"Send Click Error: {e}", device_id)
    warn("⚠ Send Button Not Found", device_id)
    return False

# =========================
# Handle Retry
# =========================

def _handle_retry(d, device_id):
    warn("Retrying Share...", device_id)
    time.sleep(1)

# =========================
# MAIN SHARE EXECUTION
# =========================

def share_post(device_id, retries=2):
    d = get_device(device_id)

    for attempt in range(1, retries + 1):
        info(f"▶ Share Post (attempt {attempt})", device_id)

        # Open Share Sheet
        if not _open_share_sheet(d, device_id):
            continue

        # Expand Share Sheet
        _expand_share_sheet(device_id)

        # Select users
        selected = _select_random_users(d, device_id)
        if selected == 0:
            warn("⚠ No Users Selected", device_id)
            time.sleep(1)
            continue

        # Send Button
        if _click_send(d, device_id):
            return True

        # Handle Retry
        _handle_retry(d, device_id)

    error("❌ Share Failed After Retries", device_id)
    return False
