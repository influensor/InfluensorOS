import time
import random
from engine.ui.device import get_device


def share_post(device_id):
    d = get_device(device_id)

    # -------------------------
    # 1️⃣ Locate Share button (paper plane)
    # -------------------------
    share_btn = d(resourceId="com.instagram.android:id/row_feed_button_share")
    if not share_btn.exists:
        share_btn = d(descriptionContains="Share")

    if not share_btn.exists:
        print(f"[{device_id}] Share button not found, skipping")
        return False

    share_btn.click()
    time.sleep(random.uniform(1.0, 1.6))

    # -------------------------
    # 2️⃣ Expand Share bottom sheet (FAST swipe / flick)
    # -------------------------
    w, h = d.window_size()

    x = w // 2
    start_y = int(h * 0.88)
    end_y = int(h * 0.55)

    # FAST flick (critical for IG)
    d.swipe(x, start_y, x, end_y, duration=0.01)
    time.sleep(random.uniform(0.6, 1.2))

    # -------------------------
    # 3️⃣ Close Share sheet (IMPORTANT)
    # -------------------------
    d.press("back")
    time.sleep(random.uniform(1.0, 1.8))

    return True
