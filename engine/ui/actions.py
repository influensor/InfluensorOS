import time
import uiautomator2 as u2

# =========================
# POST STATE CHECK (ROBUST)
# =========================

LIKE_SELECTORS = [
    # Feed posts
    {"resourceId": "com.instagram.android:id/like_button"},
    # Reels
    {"resourceId": "com.instagram.android:id/clips_like_button"},
]

def _is_any_like_button_selected(d):
    """
    Internal helper: checks known like buttons
    """
    for sel in LIKE_SELECTORS:
        btn = d(**sel)
        if btn.exists:
            try:
                info = btn.info
                # selected OR checked OR activated (Instagram varies)
                if info.get("selected") or info.get("checked") or info.get("activated"):
                    return True
            except Exception:
                pass
    return False


def is_post_liked(device_id, retries=5, delay=1.0):
    """
    Robust like-state detection with retries.
    Returns True if post is already liked.
    """
    d = u2.connect(device_id)

    for _ in range(retries):
        if _is_any_like_button_selected(d):
            return True
        time.sleep(delay)

    return False


# =========================
# DECISION GATE
# =========================
def should_skip_actions(device_id):
    """
    Returns:
        True  → Post already liked → SKIP actions but MARK delivery
        False → Safe to execute actions
    """
    return is_post_liked(device_id)
