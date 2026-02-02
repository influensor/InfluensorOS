import time
import random
from engine.ui.device import get_device


def repost_post(device_id):
    d = get_device(device_id)

    # -------------------------
    # 1️⃣ Locate Repost button
    # -------------------------
    repost_btn = d(descriptionContains="Repost")

    if not repost_btn.exists:
        print(f"[{device_id}] Repost button not found, skipping")
        return False

    # -------------------------
    # 2️⃣ Click Repost
    # -------------------------
    repost_btn.click()
    time.sleep(random.uniform(1.0, 1.8))

    # -------------------------
    # 3️⃣ Close any repost UI
    # -------------------------
    d.press("back")
    time.sleep(random.uniform(0.8, 1.5))

    return True
