import time
import random
from engine.ui.device import get_device


def save_post(device_id):
    d = get_device(device_id)

    saved = False

    # -------------------------
    # 1️⃣ Try direct Save button (bookmark)
    # -------------------------
    save_btn = d(resourceId="com.instagram.android:id/row_feed_button_save")
    if not save_btn.exists:
        save_btn = d(descriptionContains="Save")

    if save_btn.exists:
        save_btn.click()
        time.sleep(random.uniform(1.0, 2.0))
        saved = True
    else:
        # -------------------------
        # 2️⃣ Fallback: Open More (⋮) menu
        # -------------------------
        more_btn = d(descriptionContains="More")
        if not more_btn.exists:
            more_btn = d(resourceId="com.instagram.android:id/row_feed_button_more")

        if not more_btn.exists:
            print(f"[{device_id}] Save button & More menu not found, skipping")
            return False

        more_btn.click()
        time.sleep(random.uniform(1.0, 1.8))

        menu_save = d(textContains="Save")
        if not menu_save.exists:
            print(f"[{device_id}] Save option not found in menu, closing")
            d.press("back")
            time.sleep(0.8)
            return False

        menu_save.click()
        time.sleep(random.uniform(1.0, 2.0))
        saved = True

    # -------------------------
    # 3️⃣ ALWAYS close Save UI (IMPORTANT)
    # -------------------------
    #d.press("back")
    time.sleep(random.uniform(1.0, 1.8))

    return saved
