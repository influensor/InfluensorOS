import time
import random
from engine.ui.device import get_device

from engine.logger import info, warn, error


# =========================
# SELECTOR CANDIDATES
# =========================
SHARE_BUTTON_SELECTORS = [
    {"resourceId": "com.instagram.android:id/row_feed_button_share"},
    {"descriptionContains": "Share"},
    {"text": "Share"},
]


def _find_ui(d, selectors, timeout=1):
    for sel in selectors:
        ui = d(**sel)
        if ui.exists(timeout=timeout):
            return ui
    return None


# =========================
# SHARE EXECUTION
# =========================
def share_post(device_id, retries=2):
    d = get_device(device_id)

    for attempt in range(1, retries + 1):
        info(f"▶ Share Post (attempt {attempt})", device_id)

        # -------------------------
        # 1️⃣ Locate Share button
        # -------------------------
        share_btn = _find_ui(d, SHARE_BUTTON_SELECTORS)

        if not share_btn:
            warn("⚠ Share button not found", device_id)
            time.sleep(1)
            continue

        share_btn.click()
        time.sleep(random.uniform(1.0, 1.6))

        # -------------------------
        # 2️⃣ Expand Share bottom sheet (fast flick)
        # -------------------------
        w, h = d.window_size()

        x = w // 2
        start_y = int(h * 0.88)
        end_y = int(h * 0.55)

        d.swipe(x, start_y, x, end_y, duration=0.01)
        time.sleep(random.uniform(0.6, 1.2))

        # -------------------------
        # 3️⃣ Close Share sheet
        # -------------------------
        d.press("back")
        time.sleep(random.uniform(1.0, 1.8))

        info("✅ Shared Post", device_id)
        return True

    error("❌ Share failed after retries", device_id)
    return False
