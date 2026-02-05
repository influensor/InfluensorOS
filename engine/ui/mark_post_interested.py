import time
import random
from engine.ui.device import get_device


def mark_post_interested(device_id, retries=5):
    """
    Marks the currently opened post/reel as 'Interested'
    Returns True if successful, False otherwise
    """

    d = get_device(device_id)

    for attempt in range(1, retries + 1):
        # -------------------------
        # 1️⃣ Open More (⋮)
        # -------------------------
        more_btn = d(descriptionContains="More")
        if not more_btn.exists(timeout=2):
            more_btn = d(resourceId="com.instagram.android:id/row_feed_button_more")

        if not more_btn.exists(timeout=2):
            print(f"[{device_id}] More button not found (attempt {attempt})")
            time.sleep(1)
            continue

        more_btn.click()
        time.sleep(random.uniform(0.8, 1.2))

        # -------------------------
        # 2️⃣ Click Interested
        # -------------------------
        interested = d(textMatches="(?i)interested")

        if interested.exists(timeout=3):
            interested.click()
            time.sleep(random.uniform(0.6, 1.0))
            print(f"[{device_id}] Marked post as Interested")
            return True

        # -------------------------
        # 3️⃣ Cleanup if not found
        # -------------------------
        print(f"[{device_id}] Interested option not found (attempt {attempt})")
        d.press("back")
        time.sleep(1)

    return False
