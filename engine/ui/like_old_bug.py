import time
import uiautomator2 as u2

from engine.logger import info, warn, error


LIKE_BUTTON_IDS = [
    "com.instagram.android:id/like_button",
    "com.instagram.android:id/row_feed_button_like",
    "com.instagram.android:id/like_icon",
    "com.instagram.android:id/clips_like_button",
]

# =========================
# LIKE EXECUTION ONLY
# =========================
def like_post(device_id, retries=2):
    """
    Tries to like the currently opened post/reel.
    Uses multiple resource-ids + selected state.
    Returns True if like succeeded, else False.
    """

    d = u2.connect(device_id)

    for attempt in range(1, retries + 1):
        info(f"▶ Like Post (attempt {attempt})", device_id)

        like_btn = None

        # 🔍 Try all known resource-ids
        for rid in LIKE_BUTTON_IDS:
            btn = d(resourceId=rid)
            if btn.exists(timeout=0.7):
                like_btn = btn
                break

        if not like_btn:
            warn("⚠ Like button not found (all IDs)", device_id)
            time.sleep(1)
            continue

        # ✅ Already liked
        if like_btn.info.get("selected", False):
            info("✅ Already liked", device_id)
            return True

        # 👉 Perform like
        like_btn.click()
        time.sleep(1)

        # ✅ Verify again
        if like_btn.info.get("selected", False):
            info("✅ Like successful", device_id)
            return True

        warn("⚠ Like click failed, retrying", device_id)
        time.sleep(1)

    error("❌ Like failed after retries", device_id)
    return False
