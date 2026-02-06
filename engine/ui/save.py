import time
import random
from engine.ui.device import get_device

from engine.logger import info, warn, error


# =========================
# SELECTOR CANDIDATES
# =========================
SAVE_BUTTON_SELECTORS = [
    {"resourceId": "com.instagram.android:id/row_feed_button_save"},
    {"descriptionContains": "Save"},
]

MORE_BUTTON_SELECTORS = [
    {"descriptionContains": "More"},
    {"resourceId": "com.instagram.android:id/row_feed_button_more"},
]

MENU_SAVE_SELECTORS = [
    {"textContains": "Save"},
    {"text": "Save"},
]


def _find_ui(d, selectors, timeout=1):
    for sel in selectors:
        ui = d(**sel)
        if ui.exists(timeout=timeout):
            return ui
    return None


# =========================
# SAVE EXECUTION
# =========================
def save_post(device_id, retries=2):
    d = get_device(device_id)

    for attempt in range(1, retries + 1):
        info(f"▶ Save Post (attempt {attempt})", device_id)

        # -------------------------
        # 1️⃣ Try direct Save button
        # -------------------------
        save_btn = _find_ui(d, SAVE_BUTTON_SELECTORS)

        if save_btn:
            save_btn.click()
            time.sleep(random.uniform(1.0, 2.0))
            info("✅ Post saved (direct)", device_id)
            return True

        # -------------------------
        # 2️⃣ Fallback: More (⋮) menu
        # -------------------------
        more_btn = _find_ui(d, MORE_BUTTON_SELECTORS)

        if not more_btn:
            warn("⚠ Save & More not found", device_id)
            time.sleep(1)
            continue

        more_btn.click()
        time.sleep(random.uniform(1.0, 1.8))

        menu_save = _find_ui(d, MENU_SAVE_SELECTORS)

        if not menu_save:
            warn("⚠ Save option not in menu", device_id)
            d.press("back")
            time.sleep(0.8)
            continue

        menu_save.click()
        time.sleep(random.uniform(1.0, 2.0))
        info("✅ Post saved (menu)", device_id)
        return True

    error("❌ Save failed after retries", device_id)
    return False
