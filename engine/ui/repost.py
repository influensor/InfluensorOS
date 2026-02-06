import time
import random
from engine.ui.device import get_device

from engine.logger import info, warn, error


# =========================
# SELECTOR CANDIDATES
# =========================
REPOST_BUTTON_SELECTORS = [
    {"descriptionContains": "Repost"},
    {"text": "Repost"},
    {"resourceId": "com.instagram.android:id/row_feed_button_repost"},
]


def _find_ui(d, selectors, timeout=1):
    for sel in selectors:
        ui = d(**sel)
        if ui.exists(timeout=timeout):
            return ui
    return None


# =========================
# REPOST EXECUTION
# =========================
def repost_post(device_id, retries=2):
    d = get_device(device_id)

    for attempt in range(1, retries + 1):
        info(f"▶ Repost Post (attempt {attempt})", device_id)

        # -------------------------
        # 1️⃣ Locate Repost button
        # -------------------------
        repost_btn = _find_ui(d, REPOST_BUTTON_SELECTORS)

        if not repost_btn:
            warn("⚠ Repost button not found", device_id)
            time.sleep(1)
            continue

        # -------------------------
        # 2️⃣ Click Repost
        # -------------------------
        repost_btn.click()
        time.sleep(random.uniform(1.0, 1.8))

        info("✅ Reposted Post", device_id)
        return True

    error("❌ Repost failed after retries", device_id)
    return False
