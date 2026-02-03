import uiautomator2 as u2

# =========================
# POST STATE CHECK
# =========================

def is_post_liked(device_id):
    d = u2.connect(device_id)

    like_btn = d(
        resourceId="com.instagram.android:id/like_button"
    )

    if like_btn.exists(timeout=1):
        try:
            return like_btn.info.get("selected", False)
        except Exception:
            return False

    return False


# =========================
# DECISION GATE
# =========================
def should_skip_actions(device_id):
    """
    Returns:
        True  → Post already liked → SKIP all actions
        False → Safe to execute actions
    """
    return is_post_liked(device_id)
