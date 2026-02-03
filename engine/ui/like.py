import time
import uiautomator2 as u2

LIKE_BUTTON_ID = "com.instagram.android:id/like_button"

# =========================
# LIKE EXECUTION ONLY
# =========================
def like_post(device_id, retries=2):
    """
    Tries to like the currently opened post/reel.
    Assumes caller already decided that liking is allowed.
    Uses resource-id + selected state (XML-accurate).
    Returns True if like succeeded, else False.
    """

    d = u2.connect(device_id)

    for _ in range(retries):
        like_btn = d(resourceId=LIKE_BUTTON_ID)

        if not like_btn.exists(timeout=1):
            time.sleep(1)
            continue

        # ✅ Already liked
        if like_btn.info.get("selected", False):
            return True

        # 👉 Perform like
        like_btn.click()
        time.sleep(1)

        # ✅ Verify again
        if like_btn.info.get("selected", False):
            return True

        time.sleep(1)

    return False
